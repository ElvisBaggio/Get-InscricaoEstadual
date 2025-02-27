import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    TESSERACT_CMD: Optional[str] = None
    CADESP_URL: str = os.getenv('CADESP_URL', "https://www.cadesp.fazenda.sp.gov.br/(S(xxx))/Pages/Cadastro/Consultas/ConsultaPublica/ConsultaPublica.aspx")
    CHROME_DRIVER_PATH: Optional[str] = None

    # API Settings
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))
    CORS_ALLOW_ORIGINS: str = os.getenv('CORS_ALLOW_ORIGINS', '*')
    CORS_ALLOW_CREDENTIALS: bool = os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true'
    CORS_ALLOW_METHODS: str = os.getenv('CORS_ALLOW_METHODS', '*')
    CORS_ALLOW_HEADERS: str = os.getenv('CORS_ALLOW_HEADERS', '*')

    # Logging Settings
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    DATETIME_FORMAT: str = os.getenv('DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S')

    # Selenium Settings
    # Wait Timeouts
    SELENIUM_DEFAULT_WAIT_TIMEOUT: int = int(os.getenv('SELENIUM_DEFAULT_WAIT_TIMEOUT', '10'))
    SELENIUM_QUICK_WAIT_TIMEOUT: int = int(os.getenv('SELENIUM_QUICK_WAIT_TIMEOUT', '5'))
    SELENIUM_CAPTCHA_STABILITY_WAIT: float = float(os.getenv('SELENIUM_CAPTCHA_STABILITY_WAIT', '0.1'))
    SELENIUM_RETRY_DELAY: float = float(os.getenv('SELENIUM_RETRY_DELAY', '0.2'))
    SELENIUM_FORM_RETRY_DELAY: float = float(os.getenv('SELENIUM_FORM_RETRY_DELAY', '0.1'))

    # Retry Attempts
    SELENIUM_MAX_CAPTCHA_ATTEMPTS: int = int(os.getenv('SELENIUM_MAX_CAPTCHA_ATTEMPTS', '5'))
    SELENIUM_MAX_FORM_RETRIES: int = int(os.getenv('SELENIUM_MAX_FORM_RETRIES', '5'))
    SELENIUM_RESULT_RETRIES: int = int(os.getenv('SELENIUM_RESULT_RETRIES', '3'))
    SELENIUM_MIN_RESULT_SECTIONS: int = int(os.getenv('SELENIUM_MIN_RESULT_SECTIONS', '3'))
    SELENIUM_BASE_RETRY_DELAY: float = float(os.getenv('SELENIUM_BASE_RETRY_DELAY', '2.0'))

    # Browser Settings
    SELENIUM_CHROME_HEADLESS: bool = os.getenv('SELENIUM_CHROME_HEADLESS', 'true').lower() == 'true'

    # Captcha recognition settings with optimized values from calibration
    CAPTCHA_PSM_MODE: int = 7  # Single line of text
    CAPTCHA_CONTRAST: float = 2.5
    CAPTCHA_THRESHOLD: int = 128
    CAPTCHA_APPLY_NOISE_REDUCTION: bool = True
    CAPTCHA_RESIZE_SMALL_IMAGES: bool = True
    
    # Captcha attempt logging settings
    CAPTCHA_SAVE_ATTEMPTS: bool = True
    CAPTCHA_ATTEMPTS_DIR: str = "captcha_attempts"
    
    # Selenium element IDs
    # Selenium element IDs
    TYPE_SELECT_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_tipoFiltroDropDownList"
    CNPJ_INPUT_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_valorFiltroTextBox"
    CAPTCHA_IMG_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_imagemDinamica"
    CAPTCHA_INPUT_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_imagemDinamicaTextBox"
    SEARCH_BUTTON_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_consultaPublicaButton"
    # Result page selectors
    CONTROL_CODE_ID: str = "ctl00_conteudoPaginaPlaceHolder_lblCodigoControleCertidao"
    RESULT_TABLE_XPATH: str = "//table[contains(@style, 'border:1px solid gray')]"
    RESULT_SECTIONS_XPATH: str = "//td[contains(@class, 'labelHeader')]"
    
    # Data fields classes and selectors
    LABEL_CLASS: str = "labelDetalhe"
    DATA_CLASS: str = "dadoDetalhe"
    
    # XPath expressions for IE number - based on actual HTML structure
    IE_XPATH: str = "//tr/td[@class='dadoDetalhe' and preceding-sibling::td[@class='labelDetalhe' and ./b[text()='IE: ']]]"
    IE_XPATH_FALLBACK1: str = "//tr[.//td[@class='labelDetalhe']//b[contains(text(), 'IE:')]]/td[@class='dadoDetalhe']"
    IE_XPATH_FALLBACK2: str = "//td[contains(@class, 'dadoDetalhe') and preceding-sibling::td[contains(text(), 'IE:')]]"
    
    # Error handling
    ERROR_MSG_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_MensagemErroFiltroLabel"
    NOT_FOUND_MSG_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_MensagemNadaEncontradoLabel"
    LOADING_INDICATOR_ID: str = "ctl00_conteudoPaginaPlaceHolder_updateProgressPanel"
    
    # IE number validation pattern
    IE_NUMBER_PATTERN: str = r"^\d{3}\.\d{3}\.\d{3}\.\d{3}$"
    
    def __post_init__(self):
        if 'TESSERACT_CMD' in os.environ:
            self.TESSERACT_CMD = os.environ['TESSERACT_CMD']
        if 'CHROME_DRIVER_PATH' in os.environ:
            self.CHROME_DRIVER_PATH = os.environ['CHROME_DRIVER_PATH']
            
        # Load captcha settings from environment
        if 'CAPTCHA_PSM_MODE' in os.environ:
            self.CAPTCHA_PSM_MODE = int(os.environ['CAPTCHA_PSM_MODE'])
        if 'CAPTCHA_CONTRAST' in os.environ:
            self.CAPTCHA_CONTRAST = float(os.environ['CAPTCHA_CONTRAST'])
        if 'CAPTCHA_THRESHOLD' in os.environ:
            self.CAPTCHA_THRESHOLD = int(os.environ['CAPTCHA_THRESHOLD'])
        if 'CAPTCHA_APPLY_NOISE_REDUCTION' in os.environ:
            self.CAPTCHA_APPLY_NOISE_REDUCTION = os.environ['CAPTCHA_APPLY_NOISE_REDUCTION'].lower() == 'true'
        if 'CAPTCHA_RESIZE_SMALL_IMAGES' in os.environ:
            self.CAPTCHA_RESIZE_SMALL_IMAGES = os.environ['CAPTCHA_RESIZE_SMALL_IMAGES'].lower() == 'true'
        if 'CAPTCHA_SAVE_ATTEMPTS' in os.environ:
            self.CAPTCHA_SAVE_ATTEMPTS = os.environ['CAPTCHA_SAVE_ATTEMPTS'].lower() == 'true'
        if 'CAPTCHA_ATTEMPTS_DIR' in os.environ:
            self.CAPTCHA_ATTEMPTS_DIR = os.environ['CAPTCHA_ATTEMPTS_DIR']

settings = Settings()
