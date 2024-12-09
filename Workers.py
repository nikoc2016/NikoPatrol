import random
import time

from NikoKit.NikoQt.NQKernel.NQComponent.NQThreadManager import NQThreadWorker


class WorkerA(NQThreadWorker):
    def run(self):
        try:
            self.signal_started.emit()
            for i in range(1, 6):  # Loop 5 times
                if self.stop_flag:
                    break
                if not self.pause_flag:
                    # Log the progress
                    self.log("A", "STD_OUT", f"A{i}\n")
                    # Emit progress signal (optional)
                    self.signal_progress.emit(i)
                    # Randomly raise exception with 1/20 probability
                    if random.random() < 0.05:
                        raise Exception(f"Random exception occurred in WorkerA at iteration {i}")
                time.sleep(1)  # Sleep for 1 second
        except Exception as e:
            self.signal_error.emit(str(e))
        finally:
            self.signal_finished.emit()

class WorkerB(NQThreadWorker):
    def run(self):
        try:
            self.signal_started.emit()
            for i in range(1, 6):
                if self.stop_flag:
                    break
                if not self.pause_flag:
                    self.log("B", "STD_OUT", f"B{i}\n")
                    self.signal_progress.emit(i)
                    if random.random() < 0.05:
                        raise Exception(f"Random exception occurred in WorkerB at iteration {i}")
                time.sleep(1)
        except Exception as e:
            self.signal_error.emit(str(e))
        finally:
            self.signal_finished.emit()

class WorkerC(NQThreadWorker):
    def run(self):
        try:
            self.signal_started.emit()
            for i in range(1, 6):
                if self.stop_flag:
                    break
                if not self.pause_flag:
                    self.log("C", "STD_OUT", f"C{i}\n")
                    self.signal_progress.emit(i)
                    if random.random() < 0.05:
                        raise Exception(f"Random exception occurred in WorkerC at iteration {i}")
                time.sleep(1)
        except Exception as e:
            self.signal_error.emit(str(e))
        finally:
            self.signal_finished.emit()

class WorkerD(NQThreadWorker):
    def run(self):
        try:
            self.signal_started.emit()
            for i in range(1, 6):
                if self.stop_flag:
                    break
                if not self.pause_flag:
                    self.log("D", "STD_OUT", f"D{i}\n")
                    self.signal_progress.emit(i)
                    if random.random() < 0.05:
                        raise Exception(f"Random exception occurred in WorkerD at iteration {i}")
                time.sleep(1)
        except Exception as e:
            self.signal_error.emit(str(e))
        finally:
            self.signal_finished.emit()

class WorkerE(NQThreadWorker):
    def run(self):
        try:
            self.signal_started.emit()
            for i in range(1, 6):
                if self.stop_flag:
                    break
                if not self.pause_flag:
                    self.log("E", "STD_OUT", f"E{i}\n")
                    self.signal_progress.emit(i)
                    if random.random() < 0.05:
                        raise Exception(f"Random exception occurred in WorkerE at iteration {i}")
                time.sleep(1)
        except Exception as e:
            self.signal_error.emit(str(e))
        finally:
            self.signal_finished.emit()

class WorkerF(NQThreadWorker):
    def run(self):
        try:
            self.signal_started.emit()
            for i in range(1, 6):
                if self.stop_flag:
                    break
                if not self.pause_flag:
                    self.log("F", "STD_OUT", f"F{i}\n")
                    self.signal_progress.emit(i)
                    if random.random() < 0.05:
                        raise Exception(f"Random exception occurred in WorkerF at iteration {i}")
                time.sleep(1)
        except Exception as e:
            self.signal_error.emit(str(e))
        finally:
            self.signal_finished.emit()
