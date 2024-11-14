"""Этот модуль писал не я, что тут происходит я не понимаю. Нейросетевая магия."""

from pathlib import Path
import torch
import onnx
import onnxruntime as rt
from torchvision import transforms as T
from PIL import Image
from .tokenizer_base import Tokenizer
from typing import Optional, Tuple

# Параметры модели
MODEL_FILE = Path(__file__).parent / "captcha.onnx"
IMG_SIZE: Tuple[int, int] = (32, 128)
CHARSET = r"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"

# Инициализация токенизатора
tokenizer = Tokenizer(CHARSET)


# Функция для преобразования изображения
def get_transform(img_size: Tuple[int, int]) -> T.Compose:
    """Создает набор преобразований для изображения."""
    return T.Compose([
        T.Resize(img_size, T.InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(0.5, 0.5)
    ])


# Функция для перевода тензора в формат numpy
def to_numpy(tensor: torch.Tensor) -> torch.Tensor:
    """Преобразует тензор в numpy-массив."""
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()


# Класс для модели распознавания капчи
class CaptchaRecognizer:
    def __init__(self, model_file: str = MODEL_FILE, img_size: Tuple[int, int] = IMG_SIZE):
        """Инициализирует распознаватель капчи с указанной моделью."""
        self.transform = get_transform(img_size)
        self.session = self._initialize_session(model_file)

    def _initialize_session(self, model_file: str) -> Optional[rt.InferenceSession]:
        """Инициализирует сессию ONNX Runtime и проверяет модель на ошибки."""
        try:
            onnx_model = onnx.load(model_file)
            onnx.checker.check_model(onnx_model)
            return rt.InferenceSession(model_file)
        except (onnx.onnx_cpp2py_export.checker.ValidationError, RuntimeError) as e:
            print(f"Ошибка при загрузке модели: {e}")
            return None

    def predict(self, image: Image.Image) -> Optional[str]:
        """Предсказывает текст с изображения капчи."""
        if not self.session:
            print("Сессия модели не инициализирована.")
            return None

        # Подготовка изображения и выполнение предсказания
        x = self.transform(image.convert('RGB')).unsqueeze(0)
        ort_inputs = {self.session.get_inputs()[0].name: to_numpy(x)}
        logits = self.session.run(None, ort_inputs)[0]

        # Преобразование логитов в текст
        probs = torch.tensor(logits).softmax(-1)
        preds, _ = tokenizer.decode(probs)
        return preds[0]
