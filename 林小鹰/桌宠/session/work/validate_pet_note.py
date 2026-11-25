from pathlib import Path
import hashlib,json,os,subprocess,sys
root=Path('H:/0-Notes/my-notes-private')
work=Path(__file__).resolve().parent
def snapshot():
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*.md') if not any(v in p.parts for v in ['.git','.obsidian'])}
before=snapshot()
r=subprocess.run([sys.executable,'tools/validate_knowledge_base.py','--fix','--json'],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
(work/'pet-note-vault-validation.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
after=snapshot()
changed=[p for p,h in after.items() if before.get(p)!=h]
report={'exit_code':r.returncode,'derived_files_changed':changed,'output_tail':r.stdout[-1500:] if r.returncode==0 else 'Validation reported existing repository issues; inspect local log.'}
(work/'pet-note-vault-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True,indent=2))
