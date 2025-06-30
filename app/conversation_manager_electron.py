import asyncio
import json
import sys
from conversation_manager import ConversationManager

class ElectronInterface:
    def __init__(self):
        self.manager = ConversationManager(electron_communication=True)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.current_task = None

    def _send_to_electron(self, type, content):
        self.manager._send_to_electron(type, content)


    async def conversation_cycle(self):
        await self.manager.main_electron()

    async def process_command_async(self, command):
        if command == 'start_listening':
            if self.current_task and not self.current_task.done():
                self._send_to_electron("status", "already_running")
                return
            self.current_task = self.loop.create_task(self.conversation_cycle())

        elif command == 'interrupt_conversation':
            self._send_to_electron("status", "interrupt_received")
            if self.current_task and not self.current_task.done():
                await self.manager.request_stop() # Now async

            # Restart logic (ensure previous task is handled)
            if self.current_task and not self.current_task.done():
                try:
                    # Give current task a very short time to finish after request_stop
                    await asyncio.wait_for(self.current_task, timeout=0.1)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass # Expected if it's still running or gets cancelled by request_stop
                if not self.current_task.done(): # If still not done, cancel it hard
                    self.current_task.cancel()
                    try:
                        await self.current_task # Await cancellation
                    except asyncio.CancelledError:
                        pass

            self.current_task = self.loop.create_task(self.conversation_cycle())


        elif command == 'stop_conversation':
            self._send_to_electron("status", "stopping_application")
            if self.current_task and not self.current_task.done():
                await self.manager.request_stop() # Now async
                try:
                    await asyncio.wait_for(self.current_task, timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass

            if self.loop.is_running():
                self.loop.stop()

    def run(self):
        self._send_to_electron("status", "script_ready_waiting_for_commands")
        self._send_to_electron("status", "ready_to_listen")

        async def stdin_listener():
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            await self.loop.connect_read_pipe(lambda: protocol, sys.stdin)

            while not self.loop.is_closed():
                try:
                    line_bytes = await reader.readline()
                    if not line_bytes: # EOF
                        if self.loop.is_running(): self.loop.stop()
                        break
                    command = line_bytes.decode().strip()
                    if command:
                        # Schedule command processing in the loop
                        self.loop.create_task(self.process_command_async(command))
                    if not self.loop.is_running(): # Check if a command stopped the loop
                        break
                except Exception as e:
                    self._send_to_electron("error", f"Stdin listener error: {str(e)}")
                    if self.loop.is_running(): self.loop.stop() # Stop loop on error
                    break

        self.loop.create_task(stdin_listener())

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self._send_to_electron("status", "shutdown_keyboard_interrupt")
        finally:
            # Cleanup
            if self.current_task and not self.current_task.done():
                self.current_task.cancel()
                try:
                    # Run loop briefly to allow task cancellation to propagate
                    self.loop.run_until_complete(asyncio.sleep(0.1))
                except RuntimeError: # Loop already stopped
                    pass

            all_tasks = asyncio.all_tasks(loop=self.loop)
            for task in all_tasks:
                if task is not asyncio.current_task(loop=self.loop) and not task.done(): # Don't cancel self
                    task.cancel()

            # Run loop briefly to process cancellations if it's not already closed
            if not self.loop.is_closed():
                try:
                    # Gather remaining tasks to ensure they are cancelled
                    # This requires tasks to handle CancelledError gracefully
                    async def gather_cancellations():
                         await asyncio.gather(*(task for task in all_tasks if task is not asyncio.current_task(loop=self.loop)), return_exceptions=True)

                    # If loop is running, use run_until_complete. Otherwise, it might be too late.
                    if self.loop.is_running():
                         self.loop.run_until_complete(gather_cancellations())
                except RuntimeError: # Loop might be stopped by now
                    pass
                except asyncio.CancelledError: # If gather_cancellations itself is cancelled
                    pass


            if not self.loop.is_closed():
                self.loop.close()
            self._send_to_electron("status", "script_exited")

if __name__ == "__main__":
    interface = ElectronInterface()
    interface.run()
