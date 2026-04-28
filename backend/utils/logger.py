import logging
import warnings
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

# Suppress noisy library-level warnings (Numba, Librosa, Audioread)
warnings.filterwarnings("ignore")

# Define custom logging levels for the Vinyl Recommender
SYNC_LEVEL = 21
ANALYSIS_LEVEL = 22
RESULT_LEVEL = 23
AI_LEVEL = 24
SCRAPE_LEVEL = 25
DB_LEVEL = 26
AUDIO_LEVEL = 27

logging.addLevelName(SYNC_LEVEL, "SYNC")
logging.addLevelName(ANALYSIS_LEVEL, "ANALYSIS")
logging.addLevelName(RESULT_LEVEL, "RESULT")
logging.addLevelName(AI_LEVEL, "AI")
logging.addLevelName(SCRAPE_LEVEL, "SCRAPE")
logging.addLevelName(DB_LEVEL, "DB")
logging.addLevelName(AUDIO_LEVEL, "AUDIO")

def sync(self, message, *args, **kws):
    if self.isEnabledFor(SYNC_LEVEL):
        self._log(SYNC_LEVEL, message, args, **kws)

def analysis(self, message, *args, **kws):
    if self.isEnabledFor(ANALYSIS_LEVEL):
        self._log(ANALYSIS_LEVEL, message, args, **kws)

def result(self, message, *args, **kws):
    if self.isEnabledFor(RESULT_LEVEL):
        self._log(RESULT_LEVEL, message, args, **kws)

def ai(self, message, *args, **kws):
    if self.isEnabledFor(AI_LEVEL):
        self._log(AI_LEVEL, message, args, **kws)

def scrape(self, message, *args, **kws):
    if self.isEnabledFor(SCRAPE_LEVEL):
        self._log(SCRAPE_LEVEL, message, args, **kws)

def db(self, message, *args, **kws):
    if self.isEnabledFor(DB_LEVEL):
        self._log(DB_LEVEL, message, args, **kws)

def audio(self, message, *args, **kws):
    if self.isEnabledFor(AUDIO_LEVEL):
        self._log(AUDIO_LEVEL, message, args, **kws)

# Inject custom methods into the Logger class
logging.Logger.sync = sync
logging.Logger.analysis = analysis
logging.Logger.result = result
logging.Logger.ai = ai
logging.Logger.scrape = scrape
logging.Logger.db = db
logging.Logger.audio = audio

# Define a custom color theme for rich output
custom_theme = Theme({
    "logging.level.sync": "#0A37FF",     # Blue
    "logging.level.analysis": "#FF007F", # Pink
    "logging.level.result": "#009F21",   # Green
    "logging.level.ai": "#FFFA00",       # Yellow
    "logging.level.scrape": "#9400FF",   # Purple
    "logging.level.db": "#00FFED",       # Cyan
    "logging.level.audio": "#FFA221",    # Orange
    "logging.level.warning": "#FFD400",
    "logging.level.error": "#FF4300",
})

console = Console(theme=custom_theme)

handler = RichHandler(
    console=console,
    rich_tracebacks=True,
    show_time=True,
    show_level=True,
    show_path=True,
    markup=True,
    log_time_format="[%m/%d/%y %H:%M:%S]",
    omit_repeated_times=False,
)
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)

# Configure the root logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[handler],
)

# Silence noisy external libraries
quiet_loggers = [
    "urllib3", "httpx", "httpcore", "uvicorn.access", "uvicorn.error",
    "engineio.server", "socketio.server", "fastapi", "numba", "llvmlite",
    "matplotlib", "openai", "fontTools"
]
for name in quiet_loggers:
    logging.getLogger(name).setLevel(logging.WARNING)

logger = logging.getLogger("vinyl_recommender")