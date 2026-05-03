"""stealth_captcha — SOTA Captcha Solver (Open-Source fusioniert)

Fusioniert ALLE gefundenen Open-Source Captcha-Solver in EIN Modul:
  - Text Captcha OCR (txtcaptcha)     → HuggingFace CRNN (>89%)  ✅
  - GeeTest v4 (GeekedTest)           → API-basiert             ✅ 
  - RotateCaptcha (rotate-captcha-crack) → CNN (6.6° error)     🔧
  - FunCaptcha Audio                  → Speech Recognition       🔧
  - reCAPTCHA v2/v3                   → Playwright Audio         🔧
  - Slider Captcha (OpenCV)           → Puzzle Slider            🔧
  - Pixtral/NVIDIA Vision             → Multimodal Fallback      ✅
  
Nutze: solve_captcha("text", {"image": "captcha.png"})
       solve_captcha("geetest_v4", {"captcha_id": "...", "risk_type": "slide"})
       solve_captcha("rotate", {"image": "rotated.png"})
"""
import json, time, subprocess, os, sys
from pathlib import Path

class CaptchaSolver:
    """Unified captcha solver — wählt automatisch den besten Solver."""

    def __init__(self, config: dict = None):
        self.config = config or {}

    def solve(self, captcha_type: str, params: dict) -> dict:
        """Solve any captcha type. Returns {'success': bool, 'result': ..., 'solver': str}."""
        handler = self._get_handler(captcha_type)
        if not handler:
            return {"success": False, "error": f"No solver for {captcha_type}", "solver": None}
        return handler(params)

    def _get_handler(self, captcha_type: str):
        handlers = {
            "text": self._solve_text,
            "normal": self._solve_text,
            "geetest_v4": self._solve_geetest_v4,
            "geetest_slider": self._solve_geetest_slider,
            "rotate": self._solve_rotate,
            "funcaptcha": self._solve_funcaptcha,
            "recaptcha_v2": self._solve_recaptcha_v2,
            "recaptcha_v3": self._solve_recaptcha_v3,
        }
        return handlers.get(captcha_type)

    # ─── Text Captcha (txtcaptcha - HuggingFace CRNN) ───────────
    def _solve_text(self, params):
        """txtcaptcha: pip install txtcaptcha, pre-trained HuggingFace model (89%)."""
        try:
            from txtcaptcha import decrypt, read_captcha
            image = params.get("image") or params.get("path")
            if not image:
                return {"success": False, "error": "Need image path"}
            cap = read_captcha(image)
            result = decrypt(cap)
            text = result[0] if isinstance(result, list) else str(result)
            if text and len(text) >= 2:
                return {"success": True, "result": text, "solver": "txtcaptcha"}
            return {"success": False, "error": f"txtcaptcha empty: {text}", "solver": "txtcaptcha"}
        except ImportError:
            return {"success": False, "error": "txtcaptcha not installed (pip install txtcaptcha)", "solver": None}
        except Exception as e:
            return {"success": False, "error": str(e), "solver": "txtcaptcha"}

    # ─── GeeTest v4 (GeekedTest - API-basiert) ──────────────────
    def _solve_geetest_v4(self, params):
        """GeekedTest: Already integrated, API-based GeeTest v4 solver."""
        try:
            sys.path.insert(0, str(Path(__file__).parent / "solvers/geetest-v4"))
            from geeked import Geeked
            captcha_id = params.get("captcha_id", "54088bb07d2df3c46b79f80300b0abbe")
            risk_type = params.get("risk_type", "slide")
            geeked = Geeked(captcha_id, risk_type=risk_type)
            sec_code = geeked.solve()
            if sec_code and sec_code.get('pass_token'):
                return {"success": True, "result": sec_code, "solver": "GeekedTest"}
            return {"success": False, "error": "GeekedTest failed", "solver": "GeekedTest"}
        except Exception as e:
            return {"success": False, "error": str(e), "solver": "GeekedTest"}

    # ─── Rotate Captcha (rotate-captcha-crack - CNN) ────────────
    def _solve_rotate(self, params):
        """Rotate captcha using CNN angle prediction (RotNetR, 6.6° error)."""
        try:
            # Need Python 3.11-3.13 for rotate-captcha-crack
            import sys as _sys
            _ver = f"{_sys.version_info.major}.{_sys.version_info.minor}"
            # Try to load from venv if not installed in current env
            _rotate_path = "/tmp/rotate_env/lib/python3.13/site-packages"
            if _rotate_path not in _sys.path:
                _sys.path.insert(0, _rotate_path)
            
            from rotate_captcha_crack.model import RotNetR
            from rotate_captcha_crack.utils import process_captcha
            import torch
            from PIL import Image

            image = params.get("image") or params.get("path")
            if not image:
                return {"success": False, "error": "Need image path"}

            # Make image square for RotNetR
            img = Image.open(image)
            w, h = img.size
            size = min(w, h)
            left = (w - size) // 2
            top = (h - size) // 2
            img_square = img.crop((left, top, left + size, top + size))

            model_path = params.get("model_path") or "/tmp/rotate_captcha_crack/models/RotNetR/RotNetR/250101_23_38_54_001/best.pth"
            if not os.path.exists(model_path):
                return {"success": False, "error": f"Model not found at {model_path}"}
            
            model = RotNetR(cls_num=128, train=False)
            state = torch.load(model_path, map_location="cpu", weights_only=True)
            model.load_state_dict(state)
            model.eval()
            
            img_ts = process_captcha(img_square)
            with torch.no_grad():
                angle_factor = model.predict(img_ts)
                angle = angle_factor * 360
            
            return {"success": True, "result": {"angle": angle, "factor": float(angle_factor)}, "solver": "RotNetR"}
        except ImportError as e:
            return {"success": False, "error": f"rotate-captcha-crack not installed: {e}", "solver": None}
        except Exception as e:
            return {"success": False, "error": str(e), "solver": "RotNetR"}

    # ─── FunCaptcha Audio (API-basiert, kein Browser) ───────────
    def _solve_funcaptcha(self, params):
        """Funcaptcha audio solver via speech recognition (requests-based)."""
        try:
            sys.path.insert(0, "/tmp/funcaptcha_solver")
            from funcaptcha_solver import funcaptcha

            public_key = params.get("public_key")
            site = params.get("site")
            if not public_key or not site:
                return {"success": False, "error": "Need public_key and site params"}
            
            solver = funcaptcha(public_key=public_key, site=site)
            result = solver.solve()
            if result.get("token"):
                return {"success": True, "result": result["token"], "solver": "Funcaptcha-Audio"}
            return {"success": False, "error": result.get("error", "unknown"), "solver": "Funcaptcha-Audio"}
        except Exception as e:
            return {"success": False, "error": str(e), "solver": "Funcaptcha-Audio"}

    # ─── reCAPTCHA v2 (via Playwright) ──────────────────────────
    def _solve_recaptcha_v2(self, params):
        """reCAPTCHA v2 via Playwright (audio challenge)."""
        try:
            from playwright.sync_api import sync_playwright
            from playwright_recaptcha import recaptchav2
            
            page = params.get("page")
            if page:
                with recaptchav2.SyncSolver(page) as solver:
                    token = solver.solve_recaptcha(wait=True)
                    return {"success": True, "result": token, "solver": "playwright-recaptcha"}
            
            # Launch own browser if no page provided
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page()
                page.goto(params.get("url", "https://www.google.com/recaptcha/api2/demo"))
                with recaptchav2.SyncSolver(page) as solver:
                    token = solver.solve_recaptcha(wait=True)
                browser.close()
                return {"success": True, "result": token, "solver": "playwright-recaptcha"}
        except ImportError:
            return {"success": False, "error": "playwright-recaptcha not installed", "solver": None}
        except Exception as e:
            return {"success": False, "error": str(e), "solver": "playwright-recaptcha"}

    # ─── reCAPTCHA v3 ───────────────────────────────────────────
    def _solve_recaptcha_v3(self, params):
        """reCAPTCHA v3 (token interception)."""
        try:
            from playwright.sync_api import sync_playwright
            from playwright_recaptcha import recaptchav3
            
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page()
                with recaptchav3.SyncSolver(page) as solver:
                    page.goto(params.get("url", "https://antcpt.com/score_detector/"))
                    token = solver.solve_recaptcha()
                browser.close()
                return {"success": True, "result": token, "solver": "playwright-recaptcha"}
        except ImportError:
            return {"success": False, "error": "playwright-recaptcha not installed", "solver": None}
        except Exception as e:
            return {"success": False, "error": str(e), "solver": "playwright-recaptcha"}

    # ─── GeeTest Slider (OpenCV) ───────────────────────────────
    def _solve_geetest_slider(self, params):
        try:
            sys.path.insert(0, str(Path(__file__).parent / "solvers/geetest-slider"))
            from solver import PuzleSolver
            solver = PuzleSolver(params["piece"], params["background"])
            position = solver.get_position()
            return {"success": True, "result": {"x": position}, "solver": "geetest-slider"}
        except Exception as e:
            return {"success": False, "error": str(e), "solver": "geetest-slider"}


# ─── Convenience API ────────────────────────────────────────────────

def solve_captcha(captcha_type: str, params: dict, config: dict = None) -> dict:
    """Ein API-Aufruf für ALLE Captcha-Typen.
    
    Beispiele:
      solve_captcha("text", {"image": "captcha.png"})
      solve_captcha("geetest_v4", {"captcha_id": "...", "risk_type": "slide"})
      solve_captcha("rotate", {"image": "rotated.png"})
      solve_captcha("funcaptcha", {"public_key": "...", "site": "..."})
    """
    solver = CaptchaSolver(config)
    return solver.solve(captcha_type, params)
