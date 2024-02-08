import streamlit as st
import time
import requests
import os 

response = ""

st.markdown("""# Claude Compliance
            """)

st.markdown("""👋🏼 Salut, je suis Claude ton assistant Compliance. J'ai lu les sanctions 🤒 et les lignes directrices ☝🏼 ACPR. Je pense que je peux t'aider ! 
            """)

txt = st.text_area('Ta question de compliance :', '''
    Quels sont les principaux élements à prendre en compte dans une classification des risques ? 
    ''')
st.write('Mots:', len(txt.split(' ')))

if st.button('Envoie ta question !'):
    # print is visible in the server output, not in the page
    
    "OK, j'analyse ta question..."

    # Add a placeholder
    latest_iteration = st.empty()
    bar = st.progress(0)

    for i in range(100):
        # Update the progress bar with each iteration.
        latest_iteration.text(f'Iteration {i+1}')
        bar.progress(i + 1)
        time.sleep(0.2)
    
    "💡 Je crois que j'ai une réponse !"
    url = 'https://comprag-cshrkcigva-ew.a.run.app'
    end_point = 'open_ai_acpr_rag'
    
    response = requests.get(url=os.path.join(url,end_point),
                           params={'question': txt}
                           ).json()['reponse']
    

st.text_area('ta réponse:', response, height=300)
    