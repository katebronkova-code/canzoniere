import json
import os
import re
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Il Mio Canzoniere", page_icon="🎸", layout="centered"
)

# File JSON per il salvataggio persistente dei dati
DATA_FILE = "canzoniere.json"
SCALETTE_FILE = "scalette.json"


def carica_canzoni():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        for c in data:
          if "preferita" not in c:
            c["preferita"] = False
        return data
    except Exception:
      return []
  return []


def salva_canzoni(canzoni):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(canzoni, f, ensure_ascii=False, indent=4)


def carica_scalette():
  if os.path.exists(SCALETTE_FILE):
    try:
      with open(SCALETTE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return []
  return []


def salva_scalette(scalette):
  with open(SCALETTE_FILE, "w", encoding="utf-8") as f:
    json.dump(scalette, f, ensure_ascii=False, indent=4)


# ---------------------------------------------------------
# FUNZIONE DI TRASPOSIZIONE MULTI-NOTAZIONE (Inglese, Italiano, Ceco)
# ---------------------------------------------------------
def traspone_accordi(testo, semitoni, notazione):
  if semitoni == 0:
    return testo

  # Selezione delle scale e delle regole in base alla notazione scelta
  if notazione == "Italiano (Do, Re, Mi)":
    notes = [
        "Do",
        "Do#",
        "Re",
        "Re#",
        "Mi",
        "Fa",
        "Fa#",
        "Sol",
        "Sol#",
        "La",
        "La#",
        "Si",
    ]
    flat_map = {}
    chord_regex = r"\b(Do|Re|Mi|Fa|Sol|La|Si)(?:#|b)?(?:m|maj|min|dim|aug|7|9|11|13|sus|add)*\b"
  elif notazione == "Ceco (H=Si, B=Sib)":
    # In ceco: C, C#, D, D#, E, F, F#, G, G#, A, B(Sib), H(Si)
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "B", "H"]
    flat_map = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#"}
    chord_regex = (
        r"\b([A-H][#b]?)(?:m|maj|min|dim|aug|7|9|11|13|sus|add)*\b"
    )
  else:  # Inglese standard
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    flat_map = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
    chord_regex = (
        r"\b([A-G][#b]?)(?:m|maj|min|dim|aug|7|9|11|13|sus|add)*\b"
    )

  def replace_chord(match):
    accordo = match.group(0)

    for flat, sharp in flat_map.items():
      if accordo.startswith(flat):
        accordo = sharp + accordo[len(flat) :]

    sorted_notes = sorted(notes, key=len, reverse=True)
    root = None
    suffix = ""
    for note in sorted_notes:
      if accordo.startswith(note):
        root = note
        suffix = accordo[len(note) :]
        break

    if not root:
      return accordo

    idx = notes.index(root)
    new_idx = (idx + semitoni) % 12
    return notes[new_idx] + suffix

  return re.sub(chord_regex, replace_chord, testo)


# Inizializzazione dello stato
if "canzoni" not in st.session_state:
  st.session_state["canzoni"] = carica_canzoni()

if "scalette" not in st.session_state:
  st.session_state["scalette"] = carica_scalette()

# Stile visivo personalizzato per i pulsanti
st.markdown(
    """
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎸 Il Mio Canzoniere")

# Menu di navigazione nella barra laterale
menu = st.sidebar.selectbox(
    "Scegli una sezione",
    ["Sfoglia Canzoni", "Aggiungi Canzone", "Gestione Raccolte", "Crea Scaletta"],
)

st.sidebar.markdown("---")
modalita_scura = st.sidebar.toggle("🌙 Modalità Scura Testo", value=True)
st.sidebar.caption(
    f"📊 Totale brani in repertorio: **{len(st.session_state['canzoni'])}**"
)

canzoni = st.session_state["canzoni"]

raccolte_esistenti = sorted(
    list(
        set(
            c.get("raccolta", "Generale")
            for c in canzoni
            if c.get("raccolta")
        )
    )
)
if not raccolte_esistenti:
  raccolte_esistenti = ["Generale"]

# ---------------------------------------------------------
# SEZIONE 1: SFOGLIA CANZONI
# ---------------------------------------------------------
if menu == "Sfoglia Canzoni":
  st.subheader("📚 Il tuo Repertorio")

  if not canzoni:
    st.info(
        "Non hai ancora aggiunto nessuna canzone. Usa il menu a lato per"
        " aggiungerne una!"
    )
  else:
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
      ricerca = st.text_input("🔍 Cerca titolo o artista").lower()
    with col2:
      filtro_raccolta = st.selectbox(
          "📂 Raccolta", ["Tutte"] + raccolte_esistenti
      )
    with col3:
      solo_preferiti = st.checkbox("⭐ Preferiti")

    canzoni_filtrate = []
    for c in canzoni:
      match_testo = (
          ricerca in c["titolo"].lower() or ricerca in c["artista"].lower()
      )
      match_raccolta = (
          filtro_raccolta == "Tutte"
          or c.get("raccolta", "Generale") == filtro_raccolta
      )
      match_pref = not solo_preferiti or c.get("preferita", False)

      if match_testo and match_raccolta and match_pref:
        canzoni_filtrate.append(c)

    canzoni_filtrate = sorted(canzoni_filtrate, key=lambda x: x["titolo"].lower())

    st.write(f"Trovate **{len(canzoni_filtrate)}** canzoni.")
    st.divider()

    for c in canzoni_filtrate:
      stella = "⭐" if c.get("preferita", False) else "☆"
      with st.expander(
          f"{stella} **{c['titolo']}** — *{c['artista']}* ("
          f"{c.get('tonalita', 'N/D')})"
      ):
        col_info1, col_info2 = st.columns([3, 1])
        with col_info1:
          raccolta_corrente = c.get("raccolta", "Generale")
          tonalita_corrente = c.get("tonalita", "N/D")
          st.markdown(
              f"""
                    <div style="margin-bottom: 10px;">
                        <span style="background-color: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">📂 {raccolta_corrente}</span>
                        <span style="background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-left: 5px;">🎵 {tonalita_corrente}</span>
                    </div>
                    """,
              unsafe_allow_html=True,
          )
        with col_info2:
          if st.button(
              "⭐ Preferita" if not c.get("preferita") else "❌ Togli",
              key=f"pref_{c['titolo']}",
          ):
            c["preferita"] = not c.get("preferita", False)
            salva_canzoni(st.session_state["canzoni"])
            st.rerun()

        st.write("---")

        # Controlli per la trasposizione con scelta del sistema di notazione
        col_tr1, col_tr2 = st.columns(2)
        with col_tr1:
          sistema_notazione = st.selectbox(
              "🌐 Sistema Accordi",
              [
                  "Inglese (C, D, E)",
                  "Italiano (Do, Re, Mi)",
                  "Ceco (H=Si, B=Sib)",
              ],
              key=f"notazione_{c['titolo']}",
          )
        with col_tr2:
          trasponi = st.selectbox(
              "🎚️ Semitoni",
              [0, 1, 2, 3, 4, 5, 6, -1, -2, -3, -4, -5, -6],
              key=f"tr_{c['titolo']}",
              format_func=lambda x: f"{x:+d} semitoni" if x != 0 else "Originale",
          )

        testo_mostrato = c["testo"]
        if trasponi != 0:
          testo_mostrato = traspone_accordi(
              c["testo"], trasponi, sistema_notazione
          )

        # Colori box leggio
        if modalita_scura:
          bg_color = "#1e1e1e"
          text_color = "#f8f9fa"
          border_color = "#333333"
        else:
          bg_color = "#f8f9fa"
          text_color = "#212529"
          border_color = "#e9ecef"

        st.markdown(
            f"""
                <div style="
                    background-color: {bg_color}; 
                    padding: 20px; 
                    border-radius: 10px; 
                    border: 1px solid {border_color};
                    font-family: monospace;
                    white-space: pre-wrap;
                    color: {text_color};
                    font-size: 15px;
                    line-height: 1.6;
                    margin-top: 10px;
                    margin-bottom: 15px;
                ">{testo_mostrato}</div>
                """,
            unsafe_allow_html=True,
        )

        testo_esportazione = (
            f"Titolo: {c['titolo']}\nArtista: {c['artista']}\nTonalità:"
            f" {c.get('tonalita', '-')}\nRaccolta:"
            f" {c.get('raccolta', 'Generale')}\n\n{testo_mostrato}"
        )
        st.download_button(
            label="📥 Scarica Canzone (.txt)",
            data=testo_esportazione,
            file_name=f"{c['titolo']} - {c['artista']}.txt",
            mime="text/plain",
            key=f"down_{c['titolo']}",
        )

        if st.button(f"🗑️ Elimina '{c['titolo']}'", key=f"del_{c['titolo']}"):
          st.session_state["canzoni"] = [
              x for x in canzoni if x["titolo"] != c["titolo"]
          ]
          salva_canzoni(st.session_state["canzoni"])
          st.success(f"Canzone '{c['titolo']}' eliminata!")
          st.rerun()

# ---------------------------------------------------------
# SEZIONE 2: AGGIUNGI CANZONE
# ---------------------------------------------------------
elif menu == "Aggiungi Canzone":
  st.subheader("➕ Inserisci una Nuova Canzone")

  with st.form("form_aggiungi", clear_on_submit=True):
    titolo = st.text_input("Titolo della Canzone *")
    artista = st.text_input("Artista / Gruppo *")
    tonalita = st.text_input("Tonalità (es. Sol, Em, C)")
    is_preferita = st.checkbox("Segna subito come Preferita ⭐")

    opzioni_raccolta = raccolte_esistenti + ["+ Nuova Raccolta..."]
    scelta_r = st.selectbox("Raccolta", opzioni_raccolta)

    nuova_raccolta = ""
    if scelta_r == "+ Nuova Raccolta...":
      nuova_raccolta = st.text_input("Nome della nuova raccolta")

    testo = st.text_area(
        "Testo e Accordi (consigliato inserire gli accordi sopra le parole)",
        height=300,
    )

    submit = st.form_submit_button("Salva nel Canzoniere")

    if submit:
      if not titolo or not testo:
        st.error("Il Titolo e il Testo sono obbligatori!")
      else:
        if scelta_r == "+ Nuova Raccolta...":
          raccolta_finale = (
              nuova_raccolta.strip() if nuova_raccolta else "Generale"
          )
        else:
          raccolta_finale = scelta_r

        duplicata = any(
            c["titolo"].lower() == titolo.lower() for c in canzoni
        )
        if duplicata:
          st.warning(f"Esiste già una canzone con il titolo '{titolo}'.")
        else:
          nuova_canzone = {
              "titolo": titolo,
              "artista": artista if artista else "Autore Sconosciuto",
              "tonalita": tonalita if tonalita else "-",
              "raccolta": raccolta_finale,
              "testo": testo,
              "preferita": is_preferita,
          }
          st.session_state["canzoni"].append(nuova_canzone)
          salva_canzoni(st.session_state["canzoni"])
          st.success(
              f"Canzone '{titolo}' aggiunta con successo alla raccolta"
              f" '{raccolta_finale}'!"
          )

# ---------------------------------------------------------
# SEZIONE 3: GESTIONE RACCOLTE
# ---------------------------------------------------------
elif menu == "Gestione Raccolte":
  st.subheader("📂 Gestione delle tue Raccolte")

  with st.form("form_nuova_raccolta"):
    st.write("### Crea una nuova raccolta vuota")
    nome_nuova = st.text_input("Nome della nuova raccolta")
    crea_btn = st.form_submit_button("Crea Raccolta")

    if crea_btn:
      if not nome_nuova.strip():
        st.error("Inserisci un nome valido per la raccolta.")
      elif nome_nuova in raccolte_esistenti:
        st.warning("Esiste già una raccolta con questo nome.")
      else:
        canzone_dummy = {
            "titolo": f"Benvenuto in {nome_nuova}",
            "artista": "Sistema",
            "tonalita": "-",
            "raccolta": nome_nuova.strip(),
            "testo": "Canzone segnaposto. Puoi eliminarla o modificarla.",
            "preferita": False,
        }
        st.session_state["canzoni"].append(canzone_dummy)
        salva_canzoni(st.session_state["canzoni"])
        st.success(f"Raccolta '{nome_nuova.strip()}' creata con successo!")
        st.rerun()

  st.divider()

  for r in raccolte_esistenti:
    canzoni_nella_raccolta = [
        c for c in canzoni if c.get("raccolta", "Generale") == r
    ]
    num_canzoni = len(canzoni_nella_raccolta)

    with st.expander(f"📁 {r} ({num_canzoni} canzoni)"):
      col_a, col_b = st.columns(2)

      with col_a:
        nuovo_nome = st.text_input(
            "Rinomina raccolta", value=r, key=f"rename_{r}"
        )
        if st.button("Aggiorna Nome", key=f"btn_rename_{r}"):
          if nuovo_nome.strip() and nuovo_nome != r:
            for c in st.session_state["canzoni"]:
              if c.get("raccolta", "Generale") == r:
                c["raccolta"] = nuovo_nome.strip()
            salva_canzoni(st.session_state["canzoni"])
            st.success(f"Raccolta rinominata in '{nuovo_nome.strip()}'!")
            st.rerun()

      with col_b:
        st.write("")
        st.write("")
        if r != "Generale":
          if st.button(f"🗑️ Elimina Raccolta", key=f"del_rec_{r}"):
            for c in st.session_state["canzoni"]:
              if c.get("raccolta") == r:
                c["raccolta"] = "Generale"
            salva_canzoni(st.session_state["canzoni"])
            st.success(
                f"Raccolta '{r}' eliminata. Canzoni spostate in 'Generale'."
            )
            st.rerun()
        else:
          st.caption("La raccolta 'Generale' non può essere eliminata.")

# ---------------------------------------------------------
# SEZIONE 4: CREA SCALETTA
# ---------------------------------------------------------
elif menu == "Crea Scaletta":
  st.subheader("🎼 Generatore di Scalette")
  st.write(
      "Seleziona le canzoni dal tuo repertorio per creare la scaletta di una"
      " serata."
  )

  with st.form("form_scaletta"):
    nome_scaletta = st.text_input(
        "Nome della Scaletta (es. Live Acustico, Serata al Pub)"
    )
    titoli_disponibili = [c["titolo"] for c in canzoni]
    canzoni_selezionate = st.multiselect(
        "Seleziona i brani in ordine",
        titoli_disponibili,
        placeholder="Scegli le canzoni...",
    )

    salva_sc = st.form_submit_button("💾 Salva Scaletta")

    if salva_sc:
      if not nome_scaletta.strip():
        st.error("Inserisci un nome per la scaletta.")
      elif not canzoni_selezionate:
        st.warning("Seleziona almeno una canzone.")
      else:
        nuova_scaletta = {
            "titolo": nome_scaletta.strip(),
            "brani": canzoni_selezionate,
        }
        st.session_state["scalette"].append(nuova_scaletta)
        salva_scalette(st.session_state["scalette"])
        st.success(f"Scaletta '{nome_scaletta}' salvata con successo!")

  st.divider()
  st.subheader("📋 Le tue Scalette Salvate")

  scalette_esistenti = st.session_state["scalette"]
  if not scalette_esistenti:
    st.info("Non hai ancora creato nessuna scaletta.")
  else:
    for idx, sc in enumerate(scalette_esistenti):
      with st.expander(f"🎶 {sc['titolo']} ({len(sc['brani'])} brani)"):
        for i, brano_titolo in enumerate(sc["brani"], 1):
          st.write(f"**{i}.** {brano_titolo}")

        if st.button(f"🗑️ Elimina Scaletta", key=f"del_sc_{idx}"):
          st.session_state["scalette"].pop(idx)
          salva_scalette(st.session_state["scalette"])
          st.success("Scaletta eliminata!")
          st.rerun()
