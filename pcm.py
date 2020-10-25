################################################################################
# BEFORE YOU RUN, MAKE SURE YOU HAVE THE FOLLOWING LIBRARIES INSTALLED:
# pyaudio: https://people.csail.mit.edu/hubert/pyaudio/
# tkinter: https://tkdocs.com/tutorial/install.htm
# ------------------------------------------------------------------------------
# Author: Lucas de Camargo Souza
# E-Mail: lucas_camargo@hotmail.com.br
# ------------------------------------------------------------------------------
# Developed and tested on Python 3.8.5 under the OS Linux Kubuntu 20.04 64 bits
################################################################################

import pyaudio
import wave
from datetime import datetime
from threading import Thread
import tkinter as tk

# Guarda os dados relativos a uma gravacao e suas frames
# Tambem eh capaz de gerar e salvar um arquivo wav
class PcmData:
	def __init__(self, name, frames, channels, format, rate):
		self._frames = frames
		self._name = name
		self._channels = channels
		self._format = format
		self._rate = rate

	def save(self):
		wf = wave.open(self._name, 'wb')
		wf.setnchannels(self._channels)
		wf.setsampwidth(pyaudio.get_sample_size(self._format))
		wf.setframerate(self._rate)
		wf.writeframes(b''.join(self._frames))
		wf.close()



# Evento utilizado para avisar a thread de gravacao quando parar
class PcmEvent:
	def __init__(self):
		self._triggered = False

	def trigger(self):
		self._triggered = True

	def get(self):
		return self._triggered

# Classe principal: Integra os metodos de gravacao de audio da biblioteca pyaudio
class PcmAudio:
	_format = pyaudio.paInt16
	_channels = 1 # Mono
	_rate = 16000
	_chunk = int(_rate/10)
	recordingsList = []

	def __init__(self):
		self._event = PcmEvent()
		pass

	# A execucao eh feita dentro de uma thread para nao afetar a interface grafica
	def record_thread(self, name, channels, format, rate):
		audio = pyaudio.PyAudio()
		stream = audio.open(format=format, channels=channels,
							rate=rate, input=True, frames_per_buffer=int(rate/10))

		frames = []
		while(not self._event.get()):
			data = stream.read(self._chunk)
			frames.append(data)
		self._event = PcmEvent()

		stream.stop_stream()
		stream.close()
		audio.terminate()
		self.recordingsList.append(PcmData(name,frames,channels,format,rate))

	#Instancia a thread acima. A chamada simultanea desta funcao nao foi testada.
	def record(self, name=""):
		if name == "":
			name = "PcmAudio " + datetime.now().strftime("%d-%m-%Y %H-%M-%S")
		name = name + ".wav"

		rec_thread = Thread(target=self.record_thread, args=(name,self._channels,self._format,self._rate))
		rec_thread.start()
		

	# Seta o evento de parada da thread
	def stop(self):
		self._event.trigger()

	# Salva todos os audios dentro da lista. O salvamento parcial nao foi implementado
	def save(self, saveall=True):
		if(saveall):
			for i in self.recordingsList:
				i.save()
		else:
			raise NotImplementedError("Saving a specific audio data was not implemented!")

	# Limpa a lista de audios
	def clear(self):
		self.recordingsList.clear()

	# Retorna o numero de elementos de audio dentro da lista de audios
	def bufferSize(self):
		return len(self.recordingsList)


# Implementacao da interface grafica
class PcmApplication(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("PCM Audio Recorder")

		windowWidth = self.winfo_reqwidth()
		windowHeight = self.winfo_reqheight()
		# Gets both half the screen width/height and window width/height
		positionRight = int(self.winfo_screenwidth()/2 - windowWidth/2)
		positionDown = int(self.winfo_screenheight()/2 - windowHeight/2)
		self.geometry("+{}+{}".format(positionRight, positionDown))

		self.pcmAudio = PcmAudio()
		self.create_widgets()

	def mainloop(self):
		# Caso necessario, coloque aqui pre-configuracoes antes da chamada do loop
		return tk.Tk.mainloop(self)

	def create_widgets(self):
		self.button_record = tk.Button(self)
		self.button_record["text"] = "Gravar"
		self.button_record["command"] = self.startRecord
		self.button_record.grid(column=0, row=0)

		self.button_save = tk.Button(self, text="Salvar", fg="green", command=self.saveRecord)
		self.button_save.grid(column=0, row=1)

		self.button_clear = tk.Button(self, text="Limpar", command=self.clearRecordings)
		self.button_clear.grid(column=0, row=2)

		self.button_quit = tk.Button(self, text="Sair", fg="red", width=30, command=self.destroy)
		self.button_quit.grid(column=0, row=4, columnspan=2)

		self.label_count = tk.Label(self)
		self.label_count["width"] = 30
		self.updateBufferSize()
		self.label_count.grid(column=0, row=3, columnspan=2)

		
		self.drop_channels_var = tk.StringVar(self)
		self.drop_channels_var.set("Mono")
		self.drop_channels = tk.OptionMenu(self, self.drop_channels_var, "Mono", "Stereo")
		self.drop_channels.grid(column=1, row=0)

		self.drop_rate_var = tk.StringVar(self)
		self.drop_rate_var.set("16000 Hz")
		self.drop_rate = tk.OptionMenu(self, self.drop_rate_var, "8000 Hz","11025 Hz", "16000 Hz", "44100 Hz", "48000 Hz")
		self.drop_rate.grid(column=1, row=1)

		self.drop_format_var = tk.StringVar(self)
		self.drop_format_var.set("16-bit int")
		self.drop_format = tk.OptionMenu(self, self.drop_format_var, "8-bit uint", "8-bit int", "16-bit int", "24-bit int", "32-bit int", "32-bit float")
		self.drop_format.grid(column=1, row=2)
		

	def startRecord(self):
		self.button_record["text"] = "Parar"
		self.button_record["command"] = self.stopRecord
		
		if(self.drop_channels_var.get() == "Mono"):
			self.pcmAudio._channels = 1
		elif(self.drop_channels_var.get() == "Stereo"):
			self.pcmAudio._channels = 2
		else:
			self.pcmAudio._channels = 1

		if(self.drop_rate_var.get() == "8000 Hz"):
			self.pcmAudio._rate = 8000
		elif(self.drop_rate_var.get() == "11025 Hz"):
			self.pcmAudio._rate = 11025
		elif(self.drop_rate_var.get() == "16000 Hz"):
			self.pcmAudio._rate = 16000
		elif(self.drop_rate_var.get() == "44100 Hz"):
			self.pcmAudio._rate = 44100
		elif(self.drop_rate_var.get() == "48000 Hz"):
			self.pcmAudio._rate = 48000
		else:
			self.pcmAudio._rate = 16000

		if(self.drop_format_var.get() == "8-bit uint"):
			self.pcmAudio._format = pyaudio.paUInt8
		elif(self.drop_format_var.get() == "8-bit int"):
			self.pcmAudio._format = pyaudio.paInt8
		elif(self.drop_format_var.get() == "16-bit int"):
			self.pcmAudio._format = pyaudio.paInt16
		elif(self.drop_format_var.get() == "24-bit int"):
			self.pcmAudio._format = pyaudio.paInt24
		elif(self.drop_format_var.get() == "32-bit int"):
			self.pcmAudio._format = pyaudio.paInt32
		elif(self.drop_format_var.get() == "32-bit float"):
			self.pcmAudio._format = pyaudio.paFloat32
		else:
			self.pcmAudio._format = pyaudio.paInt16

		self.pcmAudio.record()

	def stopRecord(self):
		self.pcmAudio.stop()
		self.button_record["text"] = "Gravar"
		self.button_record["command"] = self.startRecord

	def saveRecord(self):
		self.pcmAudio.save(saveall=True)

	def clearRecordings(self):
		self.pcmAudio.clear()

	def updateBufferSize(self):
		self.label_count["text"] = "Gravacoes no buffer: " + str(self.pcmAudio.bufferSize())
		self.after(500,self.updateBufferSize)

if __name__=="__main__":
	app = PcmApplication()
	app.mainloop()
