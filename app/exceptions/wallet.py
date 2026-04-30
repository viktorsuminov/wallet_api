class WalletNotFoundError(Exception):
    pass


class WalletAccessDeniedError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass

class InvalidOperationError(Exception):
    pass
