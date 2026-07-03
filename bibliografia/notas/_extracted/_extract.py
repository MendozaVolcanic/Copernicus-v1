import fitz, os
base = r"C:\Users\nmend\OneDrive\Escritorio\claude\Automatizacion web\Automatizacion web\Copernicus-v1\bibliografia\pdfs"
out  = r"C:\Users\nmend\OneDrive\Escritorio\claude\Automatizacion web\Automatizacion web\Copernicus-v1\bibliografia\notas\_extracted"
files = ["Walter2023_CumbreVieja_TriStereo_InSAR.pdf","HomeReef_Tonga_2025_NatureSciRep.pdf","Etna2025_MultiPlatform_SciData.pdf","CumbreVieja_DSM_SciData.pdf","Niclos_2021_L9TIRS2_validation.pdf"]
for f in files:
    p = os.path.join(base,f)
    doc = fitz.open(p)
    text = ""
    for i,page in enumerate(doc):
        text += "\n\n=== PAGE %d ===\n"%(i+1) + page.get_text()
    outpath = os.path.join(out, f.replace(".pdf",".txt"))
    open(outpath,"w",encoding="utf-8").write(text)
    print("%s: pages=%d chars=%d" % (f, len(doc), len(text)))
