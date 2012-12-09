"""KArm errors

"""

class KArmError(Exception):
    pass

class DuplicationError(KArmError):
    pass

class NotFoundError(KArmError):
    pass