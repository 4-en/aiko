from .llama_cpp_generator import LlamaCppGenerator
from enum import Enum

# A collection of distilled deepseek models with the LLamaCppGenerator wrapper.

class DeepSeekModel(Enum):
    """
    A collection of DeepSeek models available for use.
    
    Parameters
    ----------
    Enum : str
        The model name used by the DeepSeek API.
    """
    
    R1_DISTILL_QWEN_1_5B = "unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF"
    R1_DISTILL_QWEN_7B = "unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF"
    R1_DISTILL_QWEN_14B = "unsloth/DeepSeek-R1-Distill-Qwen-14B-GGUF"
    R1_DISTILL_QWEN_32B = "unsloth/DeepSeek-R1-Distill-Qwen-32B-GGUF"

class GGUFModelNames(Enum):
    """
    A collection of GGUF models available for use.
    
    Parameters
    ----------
    Enum : str
        The model name used in the huggingface model hub.
    """
    F16 = "*F16.gguf"
    Q2_K = "*Q2_K.gguf"
    Q2_K_L = "*Q2_K_L.gguf"
    Q3_K_M = "*Q3_K_M.gguf"
    Q4_K_M = "*Q4_K_M.gguf"
    Q5_K_M = "*Q5_K_M.gguf"
    Q6_K = "*Q6_K.gguf"
    Q8_0 = "*Q8_0.gguf"


class DeepSeekR1DistillGenerator(LlamaCppGenerator):
    """
    A generator that uses the DeepSeek API to generate responses.
    """

    def __init__(self, model: DeepSeekModel=DeepSeekModel.R1_DISTILL_QWEN_7B, gguf_model: GGUFModelNames=GGUFModelNames.Q4_K_M):
        """
        Initialize the DeepSeek generator.
        
        Parameters
        ----------
        model : DeepSeekModel
            The model to use for generating responses.
        gguf_model : GGUFModelNames
            The GGUF model to use for generating responses.
        """
        super().__init__(gguf_model.value, model.value)

class DeepSeekR1DistillQwen1_5BGenerator(DeepSeekR1DistillGenerator):
    """
    A generator that uses the DeepSeek R1 Distill Qwen 1.5B model to generate responses.
    """

    def __init__(self, gguf_model: GGUFModelNames=GGUFModelNames.Q4_K_M):
        """
        Initialize the DeepSeek R1 Distill Qwen 1.5B generator.
        
        Parameters
        ----------
        gguf_model : GGUFModelNames
            The GGUF model to use for generating responses.
        """
        super().__init__(DeepSeekModel.R1_DISTILL_QWEN_1_5B, gguf_model)

class DeepSeekR1DistillQwen7BGenerator(DeepSeekR1DistillGenerator):
    """
    A generator that uses the DeepSeek R1 Distill Qwen 7B model to generate responses.
    """

    def __init__(self, gguf_model: GGUFModelNames=GGUFModelNames.Q4_K_M):
        """
        Initialize the DeepSeek R1 Distill Qwen 7B generator.
        
        Parameters
        ----------
        gguf_model : GGUFModelNames
            The GGUF model to use for generating responses.
        """
        super().__init__(DeepSeekModel.R1_DISTILL_QWEN_7B, gguf_model)

class DeepSeekR1DistillQwen14BGenerator(DeepSeekR1DistillGenerator):
    """
    A generator that uses the DeepSeek R1 Distill Qwen 14B model to generate responses.
    """

    def __init__(self, gguf_model: GGUFModelNames=GGUFModelNames.Q4_K_M):
        """
        Initialize the DeepSeek R1 Distill Qwen 14B generator.
        
        Parameters
        ----------
        gguf_model : GGUFModelNames
            The GGUF model to use for generating responses.
        """
        super().__init__(DeepSeekModel.R1_DISTILL_QWEN_14B, gguf_model)

class DeepSeekR1DistillQwen32BGenerator(DeepSeekR1DistillGenerator):
    """
    A generator that uses the DeepSeek R1 Distill Qwen 32B model to generate responses.
    """

    def __init__(self, gguf_model: GGUFModelNames=GGUFModelNames.Q4_K_M):
        """
        Initialize the DeepSeek R1 Distill Qwen 32B generator.
        
        Parameters
        ----------
        gguf_model : GGUFModelNames
            The GGUF model to use for generating responses.
        """
        super().__init__(DeepSeekModel.R1_DISTILL_QWEN_32B, gguf_model)