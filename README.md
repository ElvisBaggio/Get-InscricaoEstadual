# CADESP IE API

Uma API para consulta automatizada de Inscrição Estadual (IE) no CADESP (Cadastro de Contribuintes de ICMS) do estado de São Paulo. A aplicação utiliza Selenium para automação web e reconhecimento OCR para resolver CAPTCHAs automaticamente.

## Características

- Consulta automática de IE por CNPJ
- Resolução automática de CAPTCHA usando OCR
- API RESTful com documentação Swagger/OpenAPI
- Sistema de logging abrangente para monitoramento e debugging
- Suporte para múltiplas tentativas de CAPTCHA
- Calibração de CAPTCHA para maior precisão
- Gestão automática do navegador Chrome em modo headless

## Requisitos

- Python 3.9 ou superior
- ChromeDriver (instalado e no PATH do sistema)
- Tesseract OCR (opcional, configurável via variável de ambiente)
- Dependências Python:
  - fastapi>=0.100.0
  - uvicorn>=0.23.0
  - selenium>=4.15.0
  - pytesseract>=0.3.10
  - Pillow>=10.0.0
  - python-dotenv>=1.0.0

## Instalação

1. Clone o repositório:
```bash
git clone [url-do-repositorio]
cd Get-InscricaoEstadual
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
   - Copie o arquivo .env.example para .env
   - Ajuste as configurações conforme necessário:

```bash
# Caminhos dos executáveis (opcional)
TESSERACT_CMD=/path/to/tesseract
CHROME_DRIVER_PATH=/path/to/chromedriver

# Configurações de reconhecimento do CAPTCHA
CAPTCHA_PSM_MODE=13
CAPTCHA_CONTRAST=2.0
CAPTCHA_THRESHOLD=100
CAPTCHA_APPLY_NOISE_REDUCTION=true
CAPTCHA_RESIZE_SMALL_IMAGES=true

# Configurações de log do CAPTCHA
CAPTCHA_SAVE_ATTEMPTS=true
CAPTCHA_ATTEMPTS_DIR=captcha_attempts
```

## Uso

1. Inicie o servidor:
```bash
python main.py
```

2. Acesse a documentação da API:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Endpoint de Consulta

`GET /api/v1/ie/{cnpj}`

O CNPJ pode ser fornecido em formato raw (apenas números) ou formatado:
- `GET /api/v1/ie/12345678000199`
- `GET /api/v1/ie/12.345.678/0001-99`

#### Resposta de Sucesso
```json
{
    "ie_number": "142.615.209.115",
    "request_id": "1740608465236",
    "processing_time": "3.25s"
}
```

#### Resposta de Erro
```json
{
    "detail": "CNPJ must contain exactly 14 digits"
}
```

## Sistema de Logging

A aplicação utiliza um sistema de logging abrangente com diferentes níveis para cada componente:

- **api.log**: Registra requisições e respostas da API (INFO)
- **selenium.log**: Registra operações de automação web (DEBUG)
- **captcha.log**: Registra processamento de CAPTCHA (DEBUG)
- **app.log**: Registra eventos gerais da aplicação (INFO)

Características do logging:
- Rotação automática de arquivos (máximo 10MB)
- Mantém até 5 arquivos de backup
- Logging tanto em arquivo quanto console
- Rastreamento detalhado de erros com stack traces

## Estrutura do Projeto

```
.
├── main.py                 # Ponto de entrada da aplicação
├── requirements.txt        # Dependências do projeto
├── .env.example           # Template de configuração
├── captcha_calibration.py # Ferramenta de calibração de CAPTCHA
├── logs/                  # Diretório de logs
├── captcha_attempts/      # Armazenamento de tentativas de CAPTCHA
├── routes/
│   └── ie_routes.py       # Rotas da API
├── services/
│   ├── selenium_service.py # Serviço de automação web
│   └── captcha_service.py  # Serviço de processamento de CAPTCHA
└── utils/
    ├── config.py          # Configurações do projeto
    └── logger.py          # Configuração do sistema de logging
```

## Desenvolvimento

### Calibração de CAPTCHA

O sistema inclui uma ferramenta de calibração sofisticada para otimizar o reconhecimento de CAPTCHA:

```bash
python captcha_calibration.py
```

A ferramenta executa uma série de testes automatizados:
1. Captura múltiplas imagens de CAPTCHA do site CADESP
2. Testa diferentes configurações de processamento de imagem
3. Experimenta vários modos PSM do Tesseract OCR
4. Salva imagens de debug mostrando versões originais e processadas
5. Registra resultados de OCR para cada configuração

Configurações testadas incluem:
- PSM Mode (Page Segmentation Mode)
- Níveis de contraste (2.0 a 4.0)
- Valores de threshold (100 a 140)
- Redução de ruído com filtro mediano
- Redimensionamento de imagem para casos específicos

Os resultados são salvos no diretório 'calibration_output':
- 'original_N.png': Imagens originais do CAPTCHA
- 'debug_N_config_M.png': Imagens de debug mostrando:
  * Imagem original
  * Imagem processada
  * Resultados OCR para cada modo PSM

### Monitoramento

O sistema de logging fornece informações detalhadas sobre o funcionamento da aplicação:

- Tempo de processamento das requisições
- Taxa de sucesso do reconhecimento de CAPTCHA
- Erros e exceções com rastreamento completo
- Métricas de performance por CNPJ consultado

### Contribuindo

1. Faça um fork do projeto
2. Crie sua feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request
