import docx


def extraer_texto_docx(ruta_archivo: str) -> str:
    doc = docx.Document(ruta_archivo)
    partes = []
    for parrafo in doc.paragraphs:
        texto = parrafo.text.strip()
        if texto:
            partes.append(texto)
    return "\n".join(partes)
