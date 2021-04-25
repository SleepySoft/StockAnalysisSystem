import uuid


class TerminalContext:
    def __init__(self):
        pass

    def identifier(self) -> str:
        pass

    def push_message_handler(self, output_text: str):
        pass


class SasTerminal:

    def __init__(self):
        pass

    def interact(self, ctx: TerminalContext, input_text: str) -> str:
        self.analysis_input_text(ctx, input_text)

    def push_message(self, ctx: TerminalContext, output_text: str):
        if ctx is not None:
            ctx.push_message_handler(output_text)

    # ----------------------------------------------------------------------------------------

    def analysis_input_text(self, ctx: TerminalContext, input_text: str):
        pass

    def dispatch_command(self, ctx: TerminalContext):
        pass






