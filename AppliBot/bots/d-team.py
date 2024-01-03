import requests
from bs4 import BeautifulSoup as bs
import json
from datetime import datetime, timedelta
import PyPDF2
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import telebot

class DTeam:
    def __init__(self, email: str, password: str) -> None:
        """
        Initialize the DTeam class with the provided email and password.

        Parameters:
        - email (str): Email address for D-Team account.
        - password (str): Password for D-Team account.
        """
        self.session = self.connexion(email, password)
        self.email = email
        self.identite = None
        self.familles = None
        self.mail_adress = None
        self.mail_pwd = None        
        self.telegram_api_token = None
        self.telegram_chan_id = None

    def connexion(self, email: str, password: str) -> requests.Session:
        """
        Connect to the D-Team account.

        Parameters:
        - email (str): Email address for D-Team account.
        - password (str): Password for D-Team account.

        Returns:
        - requests.Session: Session object after successful login.
        """
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'fr',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Referer': 'https://d-team.fr/espace-membre'
        }

        session = requests.session()
        session.headers = headers

        r = session.get("https://www.d-team.fr/espace-membre")
        token = bs(r.text, "html.parser").find("input", {"name": "_token"}).get('value')

        data = {
            "_token": token,
            "email": email,
            "password": password,
            "remember": "on"
        }

        r = session.post("https://www.d-team.fr/connexion", json=data)
        cookies = [cookie.name + "=" + cookie.value for cookie in session.cookies]
        headers["Cookie"] = "; ".join(cookies)

        self.identite = bs(session.get("https://www.d-team.fr/intervenant/profile").text,
                           "html.parser").find("div", {"class": "font-medium"}).text.strip()
        print(f"Bienvenue {self.identite} tu es connecté à la dream team")
        return session

    def set_mail_credentials(self, mail_adress: str, mail_pwd: str) -> None:
        """
        register Gmail access credentials to send mail
        
        - mail_adress (str): Gmail adress to send mails.
        - mail_pwd (str): Gmail app-password. Read the docs to generate it: https://support.google.com/mail/answer/185833.
        """
        self.mail_adress = mail_adress
        self.mail_pwd = mail_pwd

    def set_telegram_credentials(self, api_token: str, chan_id: int) -> None:
        """
        register Telegram access credentials to send upcoming courses. See telegram documentation about it : https://core.telegram.org/bots
        
        - api_token (str): telegram bot token, need to create a telegram bot.
        - chan_id (int): telegram channel id, to send to a dedicated user.
        """
        self.telegram_api_token = api_token
        self.telegram_chan_id = chan_id
        

    def get_bulletins(self, tout: bool = False, name: str = None) -> io.BytesIO:
        """
        Get the bulletins as a merged PDF content.

        Parameters:
        - tout (bool): Optional, whether to fetch all bulletins.
        - name (str): Optional name filter for bulletins.

        Returns:
        - io.BytesIO: Merged PDF content and the month.
        """
        if name is None:
            r = self.session.get("https://www.d-team.fr/intervenant/bulletins?show=10000")
        else:
            r = self.session.get(f"https://www.d-team.fr/intervenant/bulletins?show=10000&search={name}")
        lignes = bs(r.text, "html.parser").find("main").find("tbody").findAll("tr")
        
        if tout:
            mois = "-"
        else:
            mois = lignes[0].find("td").text.split(" - ")[0].strip()
        merger = PyPDF2.PdfFileMerger()
        i = 0
        while i < len(lignes) and mois in lignes[i].text:
            lien = lignes[i].find("a")["href"]
            pdf_file = io.BytesIO(self.session.get(lien).content)
            merger.append(pdf_file)
            i+=1
        path = f"d-team_bulletins_{mois.replace(' ','-')}"
        if name:
            path += f"_{name}"
            
        merged_pdf_content = io.BytesIO()
        merged_pdf_content.name = f"{path}.pdf"
        merger.write(merged_pdf_content)
        merged_pdf_content.seek(0)
        merger.close()
        return merged_pdf_content

    def fetch_familles(self) -> dict: #dict[str, dict]: for python > 3.9
        """
        Fetch family information from D-Team.

        Returns:
        - dict[str, dict]: Family information in the format {name: {id, nom, adresse, enfant: {prenom, nom}}}
        """
        if self.familles:
            return self.familles
        familles = {}
        r = self.session.get("https://www.d-team.fr/intervenant/familles")
        lignes = bs(r.text, "html.parser").find("tbody").findAll("tr")
        for ligne in lignes:
            family_name = ligne.find("td",{"data-label":"Famille"}).text.strip()
            family_id = int(ligne.find("button")["wire:click"].split("(")[1][:-1])
            f = self.session.get(f"https://www.d-team.fr/intervenant/familles?id={family_id}")
            infos = bs(f.text, "html.parser").find("div",{"role":"dialog"}).findAll("li")
            infos = [info.text.split(" : ")[1] for info in infos]
            adresse = infos[3].strip() + ", " + infos[6] + " " + infos[5]
            familles[family_name] = {"id":family_id, "nom": family_name, "adresse":adresse, "enfant":{"prénom":infos[11], "nom":infos[10]}}
        self.familles = familles # put information in cache if needed later to avoid multiple calls to same endpoint.
        return familles

    def fetch_prochain_cours(self, jours: int = -1, heures: int = 0) -> list: #list[list]: for python > 3.9
        """
        Fetch upcoming courses.

        Parameters:
        - jours (int): Number of days to consider for upcoming courses.
        - heures (int): Number of hours to consider for upcoming courses.

        Returns:
        - list[list]: List of upcoming courses information.
        """
        retour = []
        r = self.session.get("https://www.d-team.fr/intervenant/cours?show=1000&status=waiting")
        lignes = bs(r.text, "html.parser").find("tbody").findAll("tr")
        now = datetime.now()
        for ligne in lignes:
            data = [td.text.strip() for td in ligne.findAll("td")[:-2]]
            date = datetime.strptime(data[3], "%d/%m/%Y %H:%M")
            data[3] = date
            data[2] = int(float(data[2].split(' ')[0])*60)
            if date - now < timedelta(days=jours, hours=heures) or jours == -1:
                retour.append(data)
        return retour

    def send_email_with_attachment(self, attachment_content: io.BytesIO) -> None:
        """
        Send an email with the PDF attachment.

        Parameters:
        - attachment_content (io.BytesIO): Merged PDF content.
        """
        if self.mail_adress is None:
            raise ValueError("The 'mail_adress' parameter is required for this method. Use set_mail_credentials method to add it.")
        if self.mail_pwd is None:
            raise ValueError("The 'mail_pwd' parameter is required for this method. Use set_mail_credentials method to add it.")
            
        msg = MIMEMultipart()

        my_address = self.mail_adress
        app_generated_password = self.mail_pwd

        msg["Subject"] = "Bulletins de paie D-team"
        msg["From"] = my_address
        msg["To"] = self.email
        body = f"Bonjour,\n\nVeuillez trouver ci-joint vos bulletins de paie D-team pour le mois de {attachment_content.name.split('_')[-1].split('.')[0].replace('-',' ')}.\n\nCordialement,\nL'équipe d'applibot"
        msg.attach(MIMEText(body, "plain"))

        attachment = MIMEBase("application", "pdf")
        attachment.set_payload(attachment_content.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename=attachment_content.name)
        msg.attach(attachment)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp: #https://support.google.com/mail/answer/185833?hl=fr-FR
            smtp.login(my_address, app_generated_password)
            smtp.send_message(msg)

    def send_telegram_notification(self, cours: list, familles: dict) -> None: #def send_telegram_notification(self, cours: list[list], familles: dict[str, dict]) -> None: for python > 3.9
        """
        Send Telegram notifications for upcoming courses.

        Parameters:
        - cours (list[list]): List of upcoming courses information.
        - familles (dict[str, dict]): Family information.
        """
        if self.telegram_api_token is None:
            raise ValueError("The 'telegram_api_token' parameter is required for this method. Use set_telegram_credentials method to add it.")
        if self.telegram_chan_id is None:
            raise ValueError("The 'telegram_chan_id' parameter is required for this method. Use set_telegram_credentials method to add it.")
        
        bot = telebot.TeleBot(self.telegram_api_token)
        for c in cours:
            for famille in familles.values():
                if famille["enfant"]["prénom"].lower() in c[0].lower() and famille["enfant"]["nom"].lower() in c[0].lower():
                    c.append(famille)
            lieu = requests.get(f"https://nominatim.openstreetmap.org/search?q={c[4]['adresse']}&format=json").json()[0]
            lieu = [lieu['lat'],lieu['lon']]
            message = f"Bonjour,\naujourd'hui tu as cours avec {c[0]} à "
            if c[3].minute > 0:
                message += c[3].strftime("%Hh%M.")
            else:
                message += c[3].strftime("%Hh.")
            bot.send_message(self.telegram_chan_id, message)
            bot.send_location(self.telegram_chan_id,lieu[0],lieu[1])

if __name__ == "__main__":
    # replace the informations here
    dt = DTeam("<D-Team Mail adress>", "<D-Team password>")
    dt.set_mail_credentials("<Sender mail adress>", "<Sender mail-app generated password>") #Read the docs to generate it: https://support.google.com/mail/answer/185833.
    dt.set_telegram_credentials("<Telegram api bot token>", <telegram channel id>) #See telegram documentation about it : https://core.telegram.org/bots.
    #
    #use the code
    attachment_content = dt.get_bulletins()
    dt.send_email_with_attachment(attachment_content)
    cours = dt.fetch_prochain_cours()
    familles = dt.fetch_familles()
    dt.send_telegram_notification(cours, familles)
