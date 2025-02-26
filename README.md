# CADESP IE API

API para consulta automática de Inscrição Estadual no CADESP utilizando Selenium e OCR.

## Requisitos

- Python 3.9+
- ChromeDriver (instalado e no PATH)
- Tesseract OCR (opcional - configurável via variável de ambiente)

## Instalação

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente (opcional):
```bash
# Se necessário, especifique o caminho do Tesseract
TESSERACT_CMD=path/to/tesseract

# Se necessário, especifique o caminho do ChromeDriver
CHROME_DRIVER_PATH=path/to/chromedriver
```

## Uso

1. Inicie o servidor:
```bash
python main.py
```

2. Acesse a API:
- Documentação Swagger: http://localhost:8000/docs
- Documentação ReDoc: http://localhost:8000/redoc

### Endpoint

`GET /api/v1/ie/{cnpj}`

Onde `cnpj` pode ser formatado ou apenas números. Exemplo:
- `GET /api/v1/ie/12345678000199`
- `GET /api/v1/ie/12.345.678/0001-99`

### Resposta

```json
{
    "success": true,
    "ie_number": "123456789",
    "cnpj": "12345678000199"
}
```

Em caso de erro:
```json
{
    "success": false,
    "error": "Mensagem de erro",
    "cnpj": "12345678000199"
}
```

## Estrutura do Projeto

```
.
├── main.py                 # Ponto de entrada da aplicação
├── requirements.txt        # Dependências do projeto
├── routes/
│   └── ie_routes.py       # Rotas da API
├── services/
│   ├── selenium_service.py # Serviço de automação web
│   └── captcha_service.py  # Serviço de processamento de CAPTCHA
└── utils/
    └── config.py          # Configurações do projeto
