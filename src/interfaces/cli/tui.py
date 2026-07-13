import asyncio

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.patch_stdout import patch_stdout


class AsyncTUI:
    """Asynchronous Terminal User Interface for human-agent interaction."""

    async def start_interactive_session(
        self, process_callback, outbound_queue: asyncio.Queue
    ) -> None:
        """Runs the interactive CLI loop.
        Using patch_stdout guarantees background logging doesn't corrupt
        typing buffers.
        """
        session = PromptSession()
        print("\n=== Receptáculo de Turing Inicializado ===")
        print(
            "Digite sua mensagem para interagir. "
            "Pressione Ctrl+C ou Ctrl+D para sair.\n"
        )

        async def consume_queue() -> None:
            while True:
                msg = await outbound_queue.get()
                print_formatted_text(
                    HTML(f"\n<ansimagenta>Agente (Proativo) > " f"</ansimagenta> {msg}")
                )

        asyncio.create_task(consume_queue())

        with patch_stdout():
            while True:
                try:
                    # Prompt input asynchronously
                    user_input = await session.prompt_async(
                        HTML("<ansigreen>Humano > </ansigreen>")
                    )
                    user_input = user_input.strip()

                    if not user_input:
                        continue

                    # Execute input processing callback
                    response = await process_callback(user_input)
                    clean_message = response.get("clean_message", "")
                    pad = response.get("pad_state")
                    attachment = response.get("attachment_state")

                    # Display formatted response to console using prompt_toolkit
                    # printer
                    print_formatted_text(
                        HTML(f"<ansicyan>Agente  > </ansicyan> {clean_message}")
                    )

                    if pad and attachment:
                        print_formatted_text(
                            HTML(
                                f"<ansigray>  [PAD: P={pad.pleasure:+.2f} "
                                f"A={pad.arousal:+.2f} D={pad.dominance:+.2f} | "
                                f"Apego: Ansiedade={attachment.separation_anxiety:.2f} "
                                f"Segurança={attachment.security_level:.2f}]"
                                f"</ansigray>\n"
                            )
                        )

                except (KeyboardInterrupt, EOFError):
                    print_formatted_text(
                        HTML(
                            "\n<ansired>Sessão CLI encerrada pelo usuário. "
                            "Desconectando...</ansired>"
                        )
                    )
                    break
