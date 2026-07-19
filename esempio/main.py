import psycopg2
from flask import Flask, render_template, request, redirect, session, send_file, jsonify, make_response
from datetime import timedelta
from flask import Response
import io  # <--- AGGIUNTO per gestire i byte in memoria
from PIL import Image  # <--- AGGIUNTO per la compressione delle immagini
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import base64
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

def invia_email(destinatario, oggetto, corpo_html):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_EMAIL
        msg["To"] = destinatario
        msg["Subject"] = oggetto
        msg["Reply-To"] = SMTP_EMAIL
        msg["List-Unsubscribe"] = f"<mailto:{SMTP_EMAIL}>"

        # Versione testo (fallback)
        corpo_testo = "Questa è una notifica del sistema prenotazioni."

        # Aggiungo sia testo che HTML
        msg.attach(MIMEText(corpo_testo, "plain"))
        msg.attach(MIMEText(corpo_html, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, destinatario, msg.as_string())
        server.quit()

        print("EMAIL INVIATA A:", destinatario)

    except Exception as e:
        print("ERRORE INVIO EMAIL:", e)

# Connessione al database
connection = psycopg2.connect(
    user="postgres.yrvunbgpaxkzyrpafumi",
    password='EsempioBase1',
    host="aws-0-eu-central-1.pooler.supabase.com",
    port=5432,
    database="postgres"
)

app = Flask(__name__)
app.secret_key = 'una-chiave-super-segreta'
app.permanent_session_lifetime = timedelta(minutes=30)

@app.context_processor
def inject_tipo_utente():
    utente = session.get("utente")
    if not utente:
        return dict(tipo_utente=None)

    cursor = connection.cursor()
    cursor.execute("SELECT tipo FROM utente WHERE email = %s", (utente,))
    row = cursor.fetchone()
    cursor.close()

    return dict(tipo_utente=row[0] if row else None)
def invia_mail_notificaadmin(email_admin, nome_prodotto, quantita, link):
    corpo_html = f"""
    <div style="font-family:Arial; padding:20px;">
        <h2 style="color:#333;">Nuova prenotazione ricevuta</h2>
        <p><strong>Prodotto:</strong> {nome_prodotto}</p>
        <p><strong>Quantità:</strong> {quantita}</p>
        <p>
            <a href="{link}" style="color:#1a73e8;">Visualizza prenotazioni</a>
        </p>
        <hr>
        <small style="color:#777;">
            Questa è una notifica automatica del sistema prenotazioni.
        </small>
    </div>
    """
    invia_email(email_admin, "Nuova prenotazione ricevuta", corpo_html)

def invia_mail_notificautente(nome_utente, email_utente, nome_prodotto, quantita, link):
    corpo_html = f"""
    <div style="font-family:Arial; padding:20px;">
        <h2 style="color:#333;">Prenotazione confermata</h2>
        <p>Ciao {nome_utente},</p>
        <p>La tua prenotazione è stata registrata correttamente.</p>
        <p><strong>Prodotto:</strong> {nome_prodotto}</p>
        <p><strong>Quantità:</strong> {quantita}</p>
        <p>
            <a href="{link}" style="color:#1a73e8;">Visualizza le tue prenotazioni</a>
        </p>
        <hr>
        <small style="color:#777;">
            Grazie per aver scelto il nostro servizio.
        </small>
    </div>
    """
    invia_email(email_utente, "Conferma prenotazione", corpo_html)

def invia_mail_ordineannullato(nome_utente, email_utente, nome_prodotto, quantita, link):
    corpo_html = f"""
    <div style="font-family:Arial; padding:20px;">
        <h2 style="color:#333;">Ordine annullato</h2>
        <p>Ciao {nome_utente},</p>
        <p>Il tuo ordine è stato annullato.</p>
        <p><strong>Prodotto:</strong> {nome_prodotto}</p>
        <p><strong>Quantità:</strong> {quantita}</p>
        <p>
            <a href="{link}" style="color:#1a73e8;">Guarda i nuovi prodotti</a>
        </p>
        <hr>
        <small style="color:#777;">
            Grazie per aver scelto il nostro servizio.
        </small>
    </div>
    """
    invia_email(email_utente, "Conferma annullamento ordine", corpo_html)   

def invia_mail_ordineannullato_admin(nome_utente, email_utente, nome_prodotto, quantita, link):
    corpo_html = f"""
    <div style="font-family:Arial; padding:20px;">
        <h2 style="color:#333;">Ordine annullato</h2>
        <p>L'utente {nome_utente} ({email_utente}) ha annullato il suo ordine.</p>
        <p><strong>Prodotto:</strong> {nome_prodotto}</p>
        <p><strong>Quantità:</strong> {quantita}</p>
        <p>
            <a href="{link}" style="color:#1a73e8;">Visualizza le prenotazioni</a>
        </p>
        <hr>
        <small style="color:#777;">
            Questa è una notifica automatica del sistema prenotazioni.
        </small>
    </div>
    """
    cursor = connection.cursor()
    cursor.execute("SELECT email FROM utente WHERE tipo = 0",)
    emails_admin = cursor.fetchall()
    for email in emails_admin:
        invia_email(email[0], "Notifica annullamento ordine", corpo_html)


def invia_mail_ordineconsegnato(nome_utente, email_utente, nome_prodotto, quantita, link):
    corpo_html = f"""
    <div style="font-family:Arial; padding:20px;">
        <h2 style="color:#333;">Ordine consegnato</h2>
        <p>Ciao {nome_utente},</p>
        <p>Il tuo ordine è stato consegnato con successo.</p>
        <p><strong>Prodotto:</strong> {nome_prodotto}</p>
        <p><strong>Quantità:</strong> {quantita}</p>
        <p>
            <a href="{link}" style="color:#1a73e8;">Guarda i nuovi prodotti</a>
        </p>
        <hr>
        <small style="color:#777;">
            Grazie per aver scelto il nostro servizio.
        </small>
    </div>
    """
    invia_email(email_utente, "Conferma consegna", corpo_html)

def invia_mail_suggerimento(nome_utente, email_admin, email_utente,
                            nome_prodotto, descrizione, prezzo, disponibilita,
                            tipo, dati, nome_file):

    # Converti AVIF / WEBP / qualsiasi formato → PNG
    try:
        img = Image.open(io.BytesIO(dati))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        dati = buffer.getvalue()
        nome_file = "allegato.png"
    except Exception:
        # Se non è un'immagine apribile, usa il file originale
        nome_file = nome_file.replace(" ", "_")

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = email_admin
    msg["Subject"] = f"Suggerimento prodotto da {nome_utente}"

    corpo_html = f"""
    <h2>Nuovo suggerimento prodotto</h2>
    <p><strong>Utente:</strong> {nome_utente}</p>
    <p><strong>Email Utente:</strong> {email_utente}</p>
    <p><strong>Prodotto suggerito:</strong> {nome_prodotto}</p>
    <p><strong>Descrizione:</strong> {descrizione}</p>
    <p><strong>Prezzo:</strong> {prezzo}</p>
    <p><strong>Disponibilità:</strong> {disponibilita}</p>
    <p><strong>Tipo:</strong> {tipo}</p>
    """

    msg.attach(MIMEText(corpo_html, "html"))

    parte = MIMEBase("application", "octet-stream")
    parte.set_payload(dati)
    encoders.encode_base64(parte)
    parte.add_header("Content-Disposition", f"attachment; filename={nome_file}")

    msg.attach(parte)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_PASSWORD)
    server.sendmail(SMTP_EMAIL, email_admin, msg.as_string())
    server.quit()


@app.route('/')
def index():
        return render_template('home.html')

@app.route('/SignUp')
def signup():
    return render_template('signup.html')

@app.route('/registrati', methods=['POST'])
def register():
    # Handle registration logic here
    nome = request.form['nome']
    email = request.form['email']
    password = request.form['psw']
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM utente WHERE email = %s", (email,))
    result = cursor.fetchone()
    if result:
       return render_template("signup.html", errore="Email già esistente")
    cursor = connection.cursor()
    cursor.execute("INSERT INTO utente (nome, email, pw) VALUES (%s, %s, %s)", (nome, email, password))
    connection.commit()
    cursor.close()
    session["utente"] = email
    session.permanent = False

    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/login')
def login():
     return render_template('accesso.html')


@app.route('/accesso', methods=['POST'])
def accesso():
    email = request.form['email']
    password = request.form['psw']
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM utente WHERE email = %s AND pw = %s", (email, password))

    result = cursor.fetchone()
    cursor.execute("SELECT tipo FROM utente WHERE email = %s", (email,))
    tipo_utente = cursor.fetchone()
    if not result:
        return render_template("accesso.html", errore="Credenziali non valide")
  
    session["utente"] = email
    session.permanent = False
    return redirect('/')


@app.route('/visualizza')
def visualizza():
    utente = None
    if "utente" in session:
        email = session["utente"]
        cursor = connection.cursor()
        cursor.execute("SELECT tipo FROM utente WHERE email = %s", (email,))
        utente = cursor.fetchone()
        cursor.close()
    cursor = connection.cursor()
    sql= """select p.id, p.nome, p.disp, p.prezzo, f.data, f.filename, f.created_at, t.nome, f.id
    from prodotto p
    inner join foto f on p.fotoid = f.id
    inner join tipo t on p.tipo = t.id"""
    cursor.execute(sql)
    prodotti = cursor.fetchall()
    cursor.execute("SELECT id, nome FROM tipo order by id")
    tipi = cursor.fetchall()
    cursor.close()
    tipo=None

    return render_template('visualizza.html', prodotti=prodotti, utente=utente, tipi=tipi, tipo_scelto=tipo)
   

@app.route('/scheda_prodotto/<int:id>')
def scheda_prodotto(id):
    prodotto=id
    utente = None
    if "utente" in session:
        email = session["utente"]
        cursor = connection.cursor()
        cursor.execute("SELECT tipo FROM utente WHERE email = %s", (email,))
        utente = cursor.fetchone()
        cursor.close()
    cursor = connection.cursor()
    sql= """select p.id, p.nome, p.disp, p.prezzo, f.data, f.filename, f.created_at, t.nome, f.id, p.dettagli
    from prodotto p
    inner join foto f on p.fotoid = f.id
    inner join tipo t on p.tipo = t.id
    where p.id = %s"""
    cursor.execute(sql, (prodotto,))
    prodotto = cursor.fetchone()
    cursor.close()
    tipo=None

    return render_template('scheda_prodotto.html', prodotto=prodotto, utente=utente)
   

@app.route("/solo_disp", methods=["POST"])
def solo_disp():
    solo_disp = request.form.get("solo_disp") == "1"

    cursor = connection.cursor()

    sql = """
        select p.id, p.nome, p.disp, p.prezzo, f.data, f.filename, f.created_at, t.nome, f.id
        from prodotto p
        inner join foto f on p.fotoid = f.id
        inner join tipo t on p.tipo = t.id
    """

    if solo_disp:
        sql += " WHERE p.disp > 0"

    cursor.execute(sql)
    prodotti = cursor.fetchall()

    cursor.execute("SELECT id, nome FROM tipo order by id")
    tipi = cursor.fetchall()
    cursor.close()

    # Recupera utente come fai in visualizza
    utente = None
    if "utente" in session:
        email = session["utente"]
        cursor = connection.cursor()
        cursor.execute("SELECT tipo FROM utente WHERE email = %s", (email,))
        utente = cursor.fetchone()
        cursor.close()

    return render_template(
        "visualizza.html",
        prodotti=prodotti,
        tipi=tipi,
        utente=utente,
        solo_disp=solo_disp,
        tipo_scelto=None
    )

@app.route("/filtratipo", methods=["POST"])
def filtratipo():
    tipo = request.form.get("nome")
    print("Tipo selezionato:", tipo)  # Debug: stampa il tipo selezionato
    cursor = connection.cursor()
    if tipo == "0":
        sql= """select p.id, p.nome, p.disp, p.prezzo, f.data, f.filename, f.created_at, t.nome, f.id
        from prodotto p
        inner join foto f on p.fotoid = f.id
        inner join tipo t on p.tipo = t.id"""
        cursor.execute(sql)
    else:
        sql= """select p.id, p.nome, p.disp, p.prezzo, f.data, f.filename, f.created_at, t.nome, f.id
        from prodotto p
        inner join foto f on p.fotoid = f.id
        inner join tipo t on p.tipo = t.id
        where t.id = %s"""
        cursor.execute(sql, (tipo,))
    
    prodotti = cursor.fetchall()
    print("Prodotti filtrati:", prodotti)  # Debug: stampa i prodotti filtrati
    cursor.execute("SELECT id, nome FROM tipo order by id")
    tipi = cursor.fetchall()
    cursor.close()
    return render_template('visualizza.html', prodotti=prodotti, tipi=tipi, utente=session.get("utente"), tipo_scelto=int(tipo))

@app.route("/filtraprezzo", methods=["POST"])
def filtraprezzo():
    opzione = request.form.get("opzione")
    cursor = connection.cursor()
    if opzione == "1":
        sql= """select p.id, p.nome, p.disp, p.prezzo, f.data, f.filename, f.created_at, t.nome, f.id
        from prodotto p
        inner join foto f on p.fotoid = f.id
        inner join tipo t on p.tipo = t.id
        order by p.prezzo asc"""
        cursor.execute(sql)
    elif opzione == "2":
        sql= """select p.id, p.nome, p.disp, p.prezzo, f.data, f.filename, f.created_at, t.nome, f.id
        from prodotto p
        inner join foto f on p.fotoid = f.id
        inner join tipo t on p.tipo = t.id
        order by p.prezzo desc"""
        cursor.execute(sql)
    prodotti = cursor.fetchall()
    tipo=None
    cursor.execute("SELECT id, nome FROM tipo order by id")
    tipi = cursor.fetchall()
    cursor.close()
    return render_template('visualizza.html', prodotti=prodotti, utente=session.get("utente"), tipi=tipi, tipo_sceltoo=int(opzione), tipo_scelto=tipo)


@app.route("/aggiungi_prodotto")
def aggiungi_prodotto():
    utente = session.get("utente")
    if utente is None:
        return redirect("/login")
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT tipo FROM utente WHERE email = %s", (utente,))
        tipo_utente = cursor.fetchone()
    finally:
        cursor.close()
        cursor.close()
        
    # Adesso funziona perché 'utente' contiene l'email sia dopo il login che dopo la registrazione
    if tipo_utente is None or tipo_utente[0]!= 1:
        return redirect("/login")
    cursor = connection.cursor()
    cursor.execute("SELECT id, nome FROM tipo")
    tipi = cursor.fetchall()
    cursor.close()
    return render_template('aggiungi_prodotto.html', tipi=tipi)


# ... [Le altre tue rotte: /, /SignUp, /registrati, /logout, /login, /accesso, /visualizza rimangono uguali] ...


@app.route("/foto/<int:id>")
def foto(id):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT data, filename
        FROM foto
        WHERE id=%s
    """, (id,))

    immagine = cursor.fetchone()
    cursor.close()

    if immagine is None:
        return "", 404

    dati = immagine[0]

    # Gestione del formato se psycopg2 restituisce i bytea come stringa hex o memoryview
    if isinstance(dati, memoryview):
        dati = dati.tobytes()
    elif isinstance(dati, str) and dati.startswith('\\x'):
        dati = bytes.fromhex(dati[2:])

    # Creiamo la risposta forzando il tipo webp (visto che ora le salviamo così)
    response = make_response(Response(dati, mimetype="image/webp"))
    
    # AGGIUNTO: Diciamo al browser di tenere l'immagine in cache per 30 giorni
    response.headers['Cache-Control'] = 'public, max-age=2592000'
    
    return response


@app.route('/aggiungi_prodotto/upload', methods=['POST'])
def upload():
    nome = request.form['nome']
    prezzo = request.form['prezzo']
    disp = request.form['disp']
    tipo = request.form['tipo']
    descrizione = request.form['descrizione']
    file = request.files['image']

    if file and file.filename != '':
        # 1. Apri l'immagine caricata usando Pillow
        img = Image.open(file.stream)
        
        # 2. (Opzionale ma consigliato) Ridimensiona l'immagine se è gigantesca
        # Se è più larga di 1200px, la rimpiccioliamo mantenendo le proporzioni
        max_width = 1200
        if img.width > max_width:
            w_percent = (max_width / float(img.width))
            h_size = int((float(img.height) * float(w_percent)))
            img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
            
        # 3. Comprimi e converti in WebP dentro un buffer in memoria
        output_buffer = io.BytesIO()
        # quality=75 è il perfetto compromesso: abbatte il peso dell'80% senza far sgranare la foto
        img.save(output_buffer, format="WEBP", quality=75)
        data = output_buffer.getvalue()
        
        # 4. Cambiamo l'estensione del nome file in .webp
        filename_originale = file.filename.rsplit('.', 1)[0]
        filename = f"{filename_originale}.webp"
    else:
        return "Nessuna immagine valida", 400

    # Inserisci la foto ottimizzata nel DB
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO foto(filename, data)
        VALUES (%s, %s)
        RETURNING id
    """, (filename, psycopg2.Binary(data))) # Usiamo psycopg2.Binary per sicurezza sui bytea

    foto_id = cursor.fetchone()[0]

    # Poi il prodotto
    cursor.execute("""
        INSERT INTO prodotto(nome, prezzo, disp, tipo, fotoid, dettagli)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (nome, prezzo, disp, tipo, foto_id, descrizione))

    connection.commit()
    cursor.close()

    return redirect('/visualizza')
@app.route('/modifica/<int:id>', methods=['GET', 'POST'])
def modifica(id):
    utente = session.get("utente")
    if utente is None:
        return redirect("/login")
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT tipo FROM utente WHERE email = %s", (utente,))
        tipo_utente = cursor.fetchone()
    finally:
        cursor.close()
        
    if tipo_utente is None or tipo_utente[0]!= 1:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("SELECT  nome, prezzo, disp, tipo, id, dettagli FROM prodotto WHERE id = %s", (id,))
    prodotto = cursor.fetchone()
    cursor.execute("SELECT id, nome FROM tipo")
    tipi = cursor.fetchall()
    cursor.close()

    if prodotto is None:
        return "Prodotto non trovato", 404

    return render_template('modifica.html', prodotto=prodotto, tipi=tipi)

@app.route('/modifica/<int:id>/upload', methods=['POST'])
def modifica_upload(id):
    nome = request.form['nome']
    prezzo = request.form['prezzo']
    disp = request.form['disp']
    tipo = request.form['tipo']
    dettagli = request.form['descrizione']
    file = request.files['image']

    cursor = connection.cursor()

    if file and file.filename != '':
        # 1. Apri l'immagine caricata usando Pillow
        img = Image.open(file.stream)
        
        # 2. (Opzionale ma consigliato) Ridimensiona l'immagine se è gigantesca
        max_width = 1200
        if img.width > max_width:
            w_percent = (max_width / float(img.width))
            h_size = int((float(img.height) * float(w_percent)))
            img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
            
        # 3. Comprimi e converti in WebP dentro un buffer in memoria
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="WEBP", quality=75)
        data = output_buffer.getvalue()
        
        # 4. Cambiamo l'estensione del nome file in .webp
        filename_originale = file.filename.rsplit('.', 1)[0]
        filename = f"{filename_originale}.webp"

        # Aggiorna la foto nel DB
        cursor.execute("""
            UPDATE foto
            SET filename=%s, data=%s
            WHERE id=(SELECT fotoid FROM prodotto WHERE id=%s)
        """, (filename, psycopg2.Binary(data), id))

    # Aggiorna il prodotto
    cursor.execute("""
        UPDATE prodotto
        SET nome=%s, prezzo=%s, disp=%s, tipo=%s, dettagli=%s
        WHERE id=%s
    """, (nome, prezzo, disp, tipo, dettagli, id))

    connection.commit()
    cursor.close()

    return redirect('/visualizza')

@app.route('/prenota/<int:id>', methods=['POST'])
def prenota(id):
    utente = session.get("utente")
    if utente is None:
        return redirect("/login")
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT id FROM utente WHERE email = %s", (utente,))
        idutente = cursor.fetchone()
    finally:
        cursor.close()
    cursor = connection.cursor()
    cursor.execute("select disp from prodotto where id = %s", (id,))
    disp = cursor.fetchone()
    if disp is None or disp[0] <= 0:
        return "Prodotto non disponibile", 400
    else:
        cursor.execute("select idutente,idprodotto, quantita, stato_prenotazione from prenotazioni where idutente = %s and idprodotto = %s", (idutente[0], id))
        row = cursor.fetchone()
        if row[3] == 'In attesa':
            qnt = row[2] + 1
            cursor.execute("UPDATE prenotazioni SET quantita = %s WHERE idutente = %s AND idprodotto = %s returning id", (qnt, idutente[0], id))
            print("Prenotazione effettuata con successo. ID prenotazione:", cursor.fetchone()[0])
        else:
            cursor.execute("INSERT INTO prenotazioni (idutente, idprodotto) VALUES (%s, %s) RETURNING id", (idutente[0], id))
            print("Prenotazione effettuata con successo. ID prenotazione:", cursor.fetchone()[0])
        disp = disp[0] - 1
        cursor.execute("UPDATE prodotto SET disp = %s WHERE id = %s", (disp, id))
        connection.commit()
    cursor.execute("SELECT nome FROM prodotto WHERE id = %s", (id,))
    nome_prodotto = cursor.fetchone()[0]
    cursor.execute("SELECT email FROM utente WHERE tipo = 1")
    admin_email = cursor.fetchone()[0]
    cursor.execute("SELECT quantita FROM prenotazioni WHERE idutente = %s AND idprodotto = %s", (idutente[0], id))
    nuova_quantita = cursor.fetchone()[0]
    cursor.execute("SELECT nome FROM utente WHERE id = %s", (idutente[0],))
    nome_utente = cursor.fetchone()[0]
    cursor.close()
    
    # INVIO MAIL
    link = "https://tuosito.it/tutteprenotazioni"
    invia_mail_notificaadmin(admin_email, nome_prodotto, nuova_quantita, link)
    link_utente = "https://tuosito.it/prenotazioni"
    invia_mail_notificautente(nome_utente, utente, nome_prodotto,nuova_quantita, link_utente)
    return redirect('/prenotazioni')

@app.route('/prenotazioni')
def prenotazioni():
    utente = session.get("utente")
    if utente is None:
        return redirect("/login")
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM utente WHERE email = %s", (utente,))
    idutente = cursor.fetchone()
    cursor.execute("SELECT id,nome FROM tipo")
    tipi = cursor.fetchall()
    cursor.execute("""select p.id, p.nome, pr.quantita, p.prezzo, f.data, f.filename, f.created_at, t.nome, f.id, pr.id, pr.stato_prenotazione
    from prodotto p
    inner join foto f on p.fotoid = f.id
    inner join tipo t on p.tipo = t.id
    inner join prenotazioni pr on p.id = pr.idprodotto
    where pr.idutente = %s""", (idutente[0],))
    prodotti = cursor.fetchall()
    cursor.close()
    return render_template('/prenotazioni.html', prodotti=prodotti, tipi=tipi)



@app.route('/eliminaprenotazione/<int:id>', methods=['POST'])
def eliminaprenotazione(id):
    utente = session.get("utente")
    if utente is None:
        return "Accesso negato", 403

    cursor = connection.cursor()

    # Recupero id utente
    cursor.execute("SELECT id, nome FROM utente WHERE email = %s", (utente,))
    idutente = cursor.fetchone()[0]
    nome_utente = cursor.fetchone()[1]

    # Recupero prenotazione
    cursor.execute("""
        SELECT idprodotto, quantita 
        FROM prenotazioni 
        WHERE id = %s AND idutente = %s
    """, (id, idutente))
    row = cursor.fetchone()

    if row is None:
        cursor.close()
        return "Prenotazione inesistente", 404

    idprodotto, quantita = row

    # Calcolo nuova quantità
    nuova_quantita = quantita - 1

    if nuova_quantita > 0:
        # UPDATE
        cursor.execute("""
            UPDATE prenotazioni 
            SET quantita = %s 
            WHERE id = %s AND idutente = %s
        """, (nuova_quantita, id, idutente))
    else:
        # DELETE
        cursor.execute("""
            UPDATE prenotazioni 
            SET stato_prenotazione = 'Annullata'
            WHERE id = %s AND idutente = %s
        """, (id, idutente))

    # Aggiorno disponibilità prodotto
    cursor.execute("UPDATE prodotto SET disp = disp + 1 WHERE id = %s returning nome", (idprodotto,))
    nome_prodotto = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    invia_mail_ordineannullato(nome_utente, utente, nome_prodotto, nuova_quantita, os.link)
    invia_mail_ordineannullato_admin(nome_utente, utente, nome_prodotto, nuova_quantita, os.link)
    return redirect('/prenotazioni')

@app.route('/tutteprenotazioni')
def tutteprenotazioni():
    if session.get("utente") is None and session.get("tipo_utente")!= 1:
        return "Accesso negato", 403
 

    cursor = connection.cursor()
    cursor.execute("""
        SELECT p.id, p.nome, pr.quantita, p.prezzo, t.nome, pr.id,
        u.nome, u.email, pr.stato_prenotazione
        FROM prodotto p
        
        INNER JOIN tipo t ON p.tipo = t.id
        INNER JOIN prenotazioni pr ON p.id = pr.idprodotto
        INNER JOIN utente u ON pr.idutente = u.id
    """)
    prodotti = cursor.fetchall()
    cursor.close()

    return render_template('/tutteprenotazioni.html', prodotti=prodotti)

@app.route('/contrassegna/<int:id>', methods=['POST'])
def contrassegna(id):
    utente = session.get("utente")
    if utente is None and session.get("tipo_utente")!= 1:
        return "Accesso negato", 403

    cursor = connection.cursor()
    

    # Recupero prenotazione
    cursor.execute("""
        SELECT idprodotto, quantita, idutente
        FROM prenotazioni 
        WHERE id = %s 
    """, (id,))
    row = cursor.fetchone()

    if row is None:
        cursor.close()
        return "Prenotazione inesistente", 404

    idprodotto, quantita, idutente_prenotazione = row

    qnt= request.form.get("quantita")
    # Calcolo nuova quantità
    nuova_quantita = quantita - int(qnt)

    if nuova_quantita > 0:
        # UPDATE
        cursor.execute("""
            UPDATE prenotazioni 
            SET quantita = %s 
            WHERE id = %s 
        """, (nuova_quantita, id,))
    else:
        # DELETE
        cursor.execute("""
            UPDATE prenotazioni 
            SET stato_prenotazione = 'Ritirata'
            WHERE id = %s 
        """, (id,))

    cursor.execute("select nome from utente where id = %s", (idutente_prenotazione,))
    nome_utente = cursor.fetchone()[0]
    cursor.execute("select email from utente where id = %s", (idutente_prenotazione,))  
    email_utente = cursor.fetchone()[0]
    cursor.execute("select nome from prodotto where id = %s", (idprodotto,))
    nome_prodotto = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    link = "https://notifiche.it/visualizza"
    invia_mail_ordineconsegnato(nome_utente, email_utente, nome_prodotto, nuova_quantita, link)


    return redirect('/tutteprenotazioni')

@app.route('/nuovotipo/')
def nuovotipo():
    utente = session.get("utente")
    if utente is None and session.get("tipo_utente")!= 1:
        return "Accesso negato", 403
    cursor = connection.cursor()
    cursor.execute("SELECT id, nome FROM tipo")
    tipi = cursor.fetchall()
    cursor.close()
    return render_template('nuovotipo.html', tipi=tipi)

@app.route('/nuovotipo/aggiungi', methods=['POST'])
def aggiungi_tipo():
    utente = session.get("utente")
    if utente is None and session.get("tipo_utente")!= 1:
        return "Accesso negato", 403
    nome_tipo = request.form['nome']
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM tipo WHERE nome = %s", (nome_tipo,))
    result = cursor.fetchone()
    if not result:
        cursor.execute("INSERT INTO tipo (nome) VALUES (%s)", (nome_tipo,))
    connection.commit()
    cursor.close()
    return redirect('/nuovotipo/')

@app.route('/elimina/<int:id>', methods=['POST'])
def elimina(id):
    utente = session.get("utente")
    if utente is None:
        return "Accesso negato", 403
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT tipo FROM utente WHERE email = %s", (utente,))
        tipo_utente = cursor.fetchone()
    finally:
        cursor.close()
        
    if tipo_utente is None or tipo_utente[0]!= 1:
        return "Accesso negato2", 403

    cursor = connection.cursor()
    cursor.execute("DELETE FROM prodotto WHERE id = %s", (id,))
    connection.commit()
    cursor.close()

    return redirect('/visualizza')

@app.route('/profilo')
def profilo():
    utente = session.get("utente")
    if utente is None:
        return "Accesso negato", 403
    cursor = connection.cursor()
    cursor.execute("SELECT nome, email, pw FROM utente WHERE email = %s", (utente,))
    dati_utente = cursor.fetchone()
    cursor.close()
    return render_template('profilo.html', dati_utente=dati_utente)

@app.route('/salva_profilo', methods=['POST'])
def salva_profilo():
    utente = session.get("utente")
    if utente is None:
        return "Accesso negato", 403

    nome = request.form['nome']
    email = request.form['email']
    password = request.form['password']

    cursor = connection.cursor()
    cursor.execute("UPDATE utente SET nome = %s, email = %s, pw = %s WHERE email = %s", (nome, email, password, utente))
    connection.commit()
    cursor.close()

    return redirect('/profilo')
@app.route('/nuovo_admin_pagina')
def nuovo_admin_pagina():
    
    return render_template('nuovo_admin.html')

@app.route('/nuovo_admin', methods=['POST'])
def nuovo_admin():
    utente = session.get("utente")
    if utente is None and session.get("tipo_utente")!= 1:
        return "Accesso negato", 403

    nome = request.form['nome']
    email = request.form['email']
    password = request.form['psw']

    cursor = connection.cursor()
    cursor.execute("INSERT INTO utente (nome, email, pw, tipo) VALUES (%s, %s, %s, %s) returning id", (nome, email, password, 1))
    id= cursor.fetchone()
   
    connection.commit()
    cursor.close()

    return redirect('/profilo')

@app.route('/suggerisci_prodotto')
def suggerisci_prodotto():
    utente = session.get("utente")
    if utente is None:
        return redirect("/login")
    return render_template('suggerisci_prodotto.html')

@app.route("/suggerimento", methods=["POST"])
def suggerimento():
    email_utente = session.get("utente")
    nome_prodotto = request.form["nome"]
    prezzo=request.form["prezzo"]
    disp=request.form["disp"]
    tipo=request.form["tipo"]
    descrizione = request.form["descrizione"]
    file = request.files["foto_suggerimento"]
    dati = file.read()
    nome_file = file.filename


    # Recupero TUTTI gli admin
    cursor = connection.cursor()
    cursor.execute("SELECT email FROM utente WHERE tipo = 1")
    emails_admin = cursor.fetchall()
    cursor.execute(("select nome from utente where email=%s"), (email_utente,))
    nome_utente=cursor.fetchone()
    cursor.close()

    # Invio a ciascun admin
    for admin_email in emails_admin:
        invia_mail_suggerimento(nome_utente, admin_email[0], email_utente,
                            nome_prodotto, descrizione, prezzo, disp, tipo,
                            dati, nome_file)

    return redirect("/")



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

