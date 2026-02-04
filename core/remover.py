from rembg import remove, new_session
from PIL import Image
import io

class BgRemover:
    def __init__(self, model_name="isnet-general-use"):
        self.current_model = model_name
        # Explicitly force CPU provider to avoid auto-detection errors
        self.session = new_session(model_name, providers=['CPUExecutionProvider'])

    def change_model(self, model_name):
        if model_name != self.current_model:
            self.current_model = model_name
            # Re-initialize session with new model
            self.session = new_session(model_name, providers=['CPUExecutionProvider'])

    def process_image(self, input_image: Image.Image, alpha_matting=True, post_process=True) -> Image.Image:
        """
        Removes the background from the given PIL Image.
        Returns a RGBA Image with transparency.
        """
        # rembg expects a PIL image or bytes. We'll pass the PIL image directly.
        
        # Base settings
        kwargs = {
            "session": self.session,
            "alpha_matting": alpha_matting,
            "post_process_mask": post_process
        }
        
        if alpha_matting:
            kwargs.update({
                "alpha_matting_foreground_threshold": 240,
                "alpha_matting_background_threshold": 10,
                "alpha_matting_erode_size": 10
            })
            
        return remove(input_image, **kwargs)

# Global instance or standalone usage
_remover = None

def remove_background(image: Image.Image, model_name="isnet-general-use", alpha_matting=True, post_process=True) -> Image.Image:
    global _remover
    if _remover is None:
        _remover = BgRemover(model_name)
    else:
        # Check if model needs changing
        _remover.change_model(model_name)
        
    return _remover.process_image(image, alpha_matting=alpha_matting, post_process=post_process)
