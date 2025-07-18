# Limpador de Bordas de PDF

App Flask que remove bordas brancas de PDFs enviados pelo usuário, com suporte ao Poppler.

## Rodar localmente

```
pip install -r requirements.txt
python app/app.py
```

## Deploy no Render

- Dockerfile com poppler-utils incluído
- `render.yaml` pronto para configurar o serviço
