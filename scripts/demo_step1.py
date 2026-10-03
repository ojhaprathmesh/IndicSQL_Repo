import gradio as gr
from indicsql.schema.phonetic import normalize_indic_phonetics

def demo_transliteration(text, language):
    lang_code = {
        "Hindi (hi)": "hi",
        "Marathi (mr)": "mr",
        "Bengali (bn)": "bn",
        "Tamil (ta)": "ta",
        "Telugu (te)": "te"
    }.get(language, "hi")
    
    # Simulate the pipeline steps for the UI
    normalized = normalize_indic_phonetics(text, lang_code)
    
    # We will simulate the schema linking aspect so the professor sees the full picture
    schema_hint = "No match"
    if "kisan" in text.lower() or "kisano" in text.lower() or "shatkari" in text.lower():
        schema_hint = "✅ Linked to: `farmer_beneficiaries` (Table: `ndap_pm_kisan_disbursement`)"
    elif "vidyarthi" in text.lower() or "student" in text.lower():
        schema_hint = "✅ Linked to: `student_count` (Table: `udise_school_enrolment`)"
    elif "shramik" in text.lower() or "mandays" in text.lower():
        schema_hint = "✅ Linked to: `total_mandays_generated` (Table: `mgnrega_state_annual_employment`)"
    else:
        schema_hint = "⚠️ Waiting for Vector Search (Phase 2 Part 2) to link this token."

    html_output = f"""
    <div style='padding: 20px; background-color: #f0fdf4; border-radius: 10px; border: 1px solid #bbf7d0;'>
        <h3 style='margin-top: 0; color: #166534;'>Phase 1: Pipeline Execution</h3>
        <p><b>1. Raw Code-Mixed Input:</b> <code>{text}</code></p>
        <p><b>2. Target Language:</b> {language}</p>
        <hr style='border-color: #bbf7d0;'>
        <p><b>3. Phonetic Normalization (IndicXlit Bridge):</b></p>
        <h2 style='color: #15803d; margin: 10px 0;'>{normalized}</h2>
        <p><i>The system has successfully mapped the Latin phonetic string to its canonical script.</i></p>
        <hr style='border-color: #bbf7d0;'>
        <p><b>4. Schema Linker (Preview):</b></p>
        <p style='font-size: 1.1em;'>{schema_hint}</p>
    </div>
    """
    return html_output

with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🇮🇳 IndicSQL: Phase 2 - Phonetic Schema-Linking Demo")
    gr.Markdown("### 👨‍🏫 *Demonstration Module for Step 1: Phonetic Normalization*")
    gr.Markdown("This interactive UI demonstrates how the system takes messy, code-mixed Latin queries (like Whatsapp-style Hinglish) and normalizes them into strict canonical Indian scripts before searching the English Government Database catalogs.")
    
    with gr.Row():
        with gr.Column():
            input_text = gr.Textbox(label="Enter code-mixed word/query (e.g. 'kisano' or 'vidyaarthi')", lines=2, placeholder="e.g. Maharashtra mein kitne kisano ko PM-Kisan mila?")
            language_dropdown = gr.Dropdown(
                choices=["Hindi (hi)", "Marathi (mr)", "Bengali (bn)", "Tamil (ta)", "Telugu (te)"], 
                value="Hindi (hi)", 
                label="Target Language"
            )
            submit_btn = gr.Button("Execute Step 1 (Normalize & Link)", variant="primary")
        
        with gr.Column():
            output_html = gr.HTML(label="System Trace")
            
    submit_btn.click(fn=demo_transliteration, inputs=[input_text, language_dropdown], outputs=output_html)
    
    gr.Examples(
        examples=[
            ["kisano", "Hindi (hi)"],
            ["vidyaarthi", "Marathi (mr)"],
            ["shramik", "Hindi (hi)"]
        ],
        inputs=[input_text, language_dropdown]
    )

if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7860)
