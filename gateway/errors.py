"""Stable public failure categories with actionable guidance."""
from enum import StrEnum


class FailureCode(StrEnum):
    INVALID_INPUT = 'INVALID_INPUT'
    UNSUPPORTED_FORMAT = 'UNSUPPORTED_FORMAT'
    MODALITY_MISMATCH = 'MODALITY_MISMATCH'
    MISSING_METADATA = 'MISSING_METADATA'
    PAIR_MISALIGNMENT = 'PAIR_MISALIGNMENT'
    MODEL_UNAVAILABLE = 'MODEL_UNAVAILABLE'
    MODEL_TIMEOUT = 'MODEL_TIMEOUT'
    LOW_CONFIDENCE = 'LOW_CONFIDENCE'
    INSUFFICIENT_EVIDENCE = 'INSUFFICIENT_EVIDENCE'
    INTERNAL_ERROR = 'INTERNAL_ERROR'


class InputError(ValueError):
    def __init__(self, message, code=FailureCode.INVALID_INPUT, suggestion=None):
        super().__init__(message)
        self.code = str(code)
        self.suggestion = suggestion or 'Check the image metadata and input options, then retry.'

    def as_dict(self):
        return {'status': 'INCOMPATIBLE', 'code': self.code, 'message': str(self),
                'suggestion': self.suggestion, 'blocking_errors':[{'code':self.code,'message':str(self)}],
                'actions_taken':[], 'warnings':[]}
