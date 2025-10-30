import logging
import os
from datetime import datetime

_logger_configured = False

def setup_logging(log_dir="logs", log_level=logging.INFO):
    """
    Configura el sistema de logging para el proyecto.
    
    Args:
        log_dir: Directorio donde se guardarán los logs
        log_level: Nivel mínimo de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global _logger_configured
    if _logger_configured:
        return

    # Crear directorio de logs si no existe
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Formato de los mensajes de log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configurar el logger root
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Handler para archivo general (INFO y superiores)
    info_handler = logging.FileHandler(
        os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log'),
        encoding='utf-8'
    )
    info_handler.setLevel(log_level)
    info_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(info_handler)
    
    # Handler para archivo de errores (ERROR y CRITICAL)
    error_handler = logging.FileHandler(
        os.path.join(log_dir, f'errors_{datetime.now().strftime("%Y%m%d")}.log'),
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(error_handler)
    
    # Handler para archivo de debug (todos los niveles)
    debug_handler = logging.FileHandler(
        os.path.join(log_dir, f'debug_{datetime.now().strftime("%Y%m%d")}.log'),
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(debug_handler)
    
    # Handler para consola (INFO y superiores)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    _logger_configured = True

# Llama a la configuración una vez cuando el módulo es importado por primera vez.
setup_logging()


def get_logger(name):
    """
    Obtiene un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger (generalmente __name__)
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)
