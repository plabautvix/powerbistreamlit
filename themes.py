import streamlit as st

def render_change_theme_button():
    ms = st.session_state
    if "themes" not in ms: 
        ms.themes = {"current_theme": "dark",
                            "refreshed": True,
                            
                            "light": {"theme.base": "dark",
                                    "theme.backgroundColor": "black",
                                    "theme.primaryColor": "#c98bdb",
                                    "theme.secondaryBackgroundColor": "#5591f5",
                                    "theme.textColor": "white",
                                    "theme.textColor": "white",
                                    "button_face": "🌜"},

                            "dark":  {"theme.base": "light",
                                    "theme.backgroundColor": "white",
                                    "theme.primaryColor": "#5591f5",
                                    "theme.secondaryBackgroundColor": "#ebebeb",
                                    "theme.textColor": "#0a1464",
                                    "button_face": "🌞"},
                            }
  

    def ChangeTheme():
        previous_theme = ms.themes["current_theme"]
        tdict = ms.themes["light"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]
        for vkey, vval in tdict.items(): 
            if vkey.startswith("theme"): st._config.set_option(vkey, vval)

        ms.themes["refreshed"] = False
        if previous_theme == "dark": ms.themes["current_theme"] = "light"
        elif previous_theme == "light": ms.themes["current_theme"] = "dark"

    if "first_entry_theme" not in ms:
        ChangeTheme()
        st.session_state.first_entry_theme = True

    btn_face = ms.themes["light"]["button_face"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]["button_face"]
    st.button(btn_face, on_click=ChangeTheme, use_container_width=True)

    if ms.themes["refreshed"] == False:
        ms.themes["refreshed"] = True
        st.rerun()
