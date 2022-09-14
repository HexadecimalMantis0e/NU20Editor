import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import struct
import io

class NU20Editor:
    def __init__(self, window):
        window.title("NU20Editor")
        self.currentTexture = None
        self.menuBar = tk.Menu(window)
        self.fileMenu = tk.Menu(self.menuBar, tearoff = 0)
        self.fileMenu.add_command(label = "Open NU20", command = lambda: self.openNU20())
        self.fileMenu.add_command(label = "Save NU20", state = "disabled", command = lambda: self.saveNU20())
        self.fileMenu.add_command(label = "Extract Texture", state = "disabled", command = lambda: self.extractTexture())
        self.menuBar.add_cascade(label = "File", menu = self.fileMenu)
        self.editMenu = tk.Menu(self.menuBar, tearoff = 0)
        self.editMenu.add_command(label = "Replace Texture", state = "disabled", command = lambda: self.replaceTexture())
        self.menuBar.add_cascade(label = "Edit", menu = self.editMenu)
        window.config(menu = self.menuBar)
        self.textureFrame = tk.LabelFrame(window, borderwidth = 0, highlightthickness = 0)
        self.textureFrame.grid(row = 0, column = 0, sticky = "NW")
        self.listLabel = tk.Label(self.textureFrame, text = "Select Texture: ")
        self.listLabel.grid(row = 0, column = 0, sticky = 'W')
        self.listNumber = tk.StringVar()
        self.listDropDown = ttk.Combobox(self.textureFrame, width = 4, textvariable = self.listNumber)
        self.listDropDown["values"]
        self.listDropDown.grid(row = 0, column = 1)
        self.listDropDown.bind("<<ComboboxSelected>>", self.loadTextureEvent)
        self.textureInfoFrame = tk.LabelFrame(self.textureFrame, relief = "sunken")
        self.textureInfoFrame.grid(row = 1, column = 0, columnspan = 2, sticky = "WE")
        self.heightLabel = tk.Label(self.textureInfoFrame, text = "Height: ")
        self.heightLabel.grid(row = 0, column = 0, sticky= 'W')
        self.widthLabel = tk.Label(self.textureInfoFrame, text = "Width: ")
        self.widthLabel.grid(row = 1, column = 0, sticky = 'W')
        self.mipsLabel = tk.Label(self.textureInfoFrame, text = "Mips: ")
        self.mipsLabel.grid(row = 2, column = 0, sticky = 'W')
        self.typeLabel = tk.Label(self.textureInfoFrame, text = "Type: ")
        self.typeLabel.grid(row = 3, column = 0, sticky = 'W')
        self.addressLabel = tk.Label(self.textureInfoFrame, text = "Address: ")
        self.addressLabel.grid(row = 4, column = 0, sticky = 'W')
        self.canvasFrame = tk.LabelFrame(window, relief = "sunken")
        self.canvasFrame.grid(row = 0, column = 1)
        self.textureCanvas = tk.Canvas(self.canvasFrame, bg = "gray", highlightthickness = 0, height = 522, width = 522)
        self.textureCanvas.grid(row = 0, column = 0)
        self.textureCanvas.bind("<B1-Motion>", self.moveTextureEvent)

    def clearData(self):
        self.fb = io.BytesIO()
        self.currentTexture = None
        self.listDropDown.set("")
        self.listDropDown["values"] = []
        self.heightLabel.config(text = "Height: ")
        self.widthLabel.config(text = "Width: ")
        self.mipsLabel.config(text = "Mips: ")
        self.typeLabel.config(text = "Type: ")
        self.addressLabel.config(text = "Address: ")
        self.textureCanvas.delete("all")
        self.fileMenu.entryconfig("Save NU20", state = "disabled")
        self.fileMenu.entryconfig("Extract Texture", state = "disabled")
        self.editMenu.entryconfig("Replace Texture", state = "disabled")

    def openNU20(self):
        filePath = filedialog.askopenfile(mode = "rb", filetypes = (("Bionicle Heroes NU20", "*.nup *.hgp"), ("All Files", "*.*")))

        if filePath:
            self.fileName = os.path.basename(filePath.name)
            magic = struct.unpack("<I", filePath.read(4))[0]

            if magic == 0x3032554E:
                filePath.seek(0x00, os.SEEK_SET)
                fileBytes = filePath.read()
                filePath.close()
                self.processNup(fileBytes)
            else:
                magic = struct.unpack("<I", filePath.read(4))[0]

                if magic == 0x3032554E:
                    filePath.seek(0x00, os.SEEK_SET)
                    fileBytes = filePath.read()
                    filePath.close()
                    self.processHgp(fileBytes)
                else:
                    msgBox = messagebox.showerror("Error", "Selected file is not a NU20 archive! It will not be loaded!")
                    filePath.close()
                    self.clearData()

    def linearScan(self, filePointer):
        searchFlag = False
        fileSizeDiv = self.getFileSize(filePointer) // 0x04

        for i in range(0, fileSizeDiv):
            scan = struct.unpack("<I", filePointer.read(4))[0]

            if scan == 0x30545354:
                index = filePointer.tell() - 0x04
                searchFlag = True
                break

        if searchFlag == True:
            return index
        else:
            return None

    def getFileSize(self, filePointer):
        filePointer.seek(0x00, os.SEEK_END)
        fileSize = filePointer.tell()
        filePointer.seek(0x00, os.SEEK_SET)
        return fileSize

    def processNup(self, fileBytes):
        self.fb = io.BytesIO(fileBytes)
        self.indexLocation = self.linearScan(self.fb)

        if self.indexLocation is None:
            msgBox = messagebox.showerror("Error", "Texture index not found in NUP archive!")
            self.clearData()
        else:
            self.loadNU20()

    def processHgp(self, fileBytes):
        self.fb = io.BytesIO(fileBytes)
        self.fb.seek(0x0C, os.SEEK_SET)
        self.indexLocation = struct.unpack("<I", self.fb.read(4))[0]
        self.loadNU20()

    def loadNU20(self):
        self.fb.seek(self.indexLocation, os.SEEK_SET)
        self.fb.seek(0x08, os.SEEK_CUR)
        self.indexCount = struct.unpack("<I", self.fb.read(4))[0]

        if self.indexCount == 0x00:
            msgBox = messagebox.showerror("Error", "No textures in index!")
            self.clearData()
        else:
            self.fb.seek(0x08, os.SEEK_CUR)
            self.indexSize = struct.unpack("<I", self.fb.read(4))[0]
            self.fb.seek(0x08, os.SEEK_CUR)
            self.entryList = []
            self.imageList = []
            imageListCount = []

            for i in range(0, self.indexCount):
                entryLocation = self.fb.tell()
                entryWidth = struct.unpack("<I", self.fb.read(4))[0]
                entryHeight = struct.unpack("<I", self.fb.read(4))[0]
                entryMips = struct.unpack("<I", self.fb.read(4))[0]
                self.fb.seek(0x04, os.SEEK_CUR)
                entryAddress = struct.unpack("<I", self.fb.read(4))[0]

                if ((entryWidth != 0x00) and (entryHeight != 0x00)):
                    self.entryList.append(entryLocation)
                    self.imageList.append(entryAddress)
            # enable the menuBar options
            self.fileMenu.entryconfig("Save NU20", state = "active")
            self.fileMenu.entryconfig("Extract Texture", state = "active")
            self.editMenu.entryconfig("Replace Texture", state = "active")
            # Init the dropdown
            for i in range(0, len(self.imageList)):
                imageListCount.append(i + 1)

            self.listDropDown["values"] = imageListCount
            self.listDropDown.current(0)
            self.loadTexture()

    def loadTexture(self):
        self.ddsNumber = int(self.listDropDown.get())
        self.ddsEntry = self.entryList[self.ddsNumber - 1]
        self.ddsLocation = self.imageList[self.ddsNumber - 1] + self.indexLocation + self.indexSize + 0x08
        self.fb.seek(self.ddsLocation, os.SEEK_SET)
        self.fb.seek(0x0C, os.SEEK_CUR)
        ddsHeight = struct.unpack("<I", self.fb.read(4))[0]
        ddsWidth = struct.unpack("<I", self.fb.read(4))[0]
        self.fb.seek(0x08, os.SEEK_CUR)
        ddsMips = struct.unpack("<I", self.fb.read(4))[0]
        self.fb.seek(0x34, os.SEEK_CUR)
        ddsType = self.fb.read(0x04).decode()
        self.fb.seek(-0x58, os.SEEK_CUR)
        self.heightLabel.config(text = "Height: " + str(ddsHeight))
        self.widthLabel.config(text = "Width: " + str(ddsWidth))
        self.mipsLabel.config(text = "Mips: " + str(ddsMips))
        self.typeLabel.config(text = "Type: " + str(ddsType))
        self.addressLabel.config(text = "Address: " + str(hex(self.ddsLocation)))

        if ddsMips == 0x00:
            self.currentSize = (ddsWidth * ddsHeight * 0x06 ) + 0x80
        else:
            self.currentSize = (ddsWidth * ddsHeight) + 0x80

            for i in range(1, ddsMips):
                ddsHeight //= 0x02
                ddsWidth //= 0x02
                self.currentSize += max(0x01, ((ddsWidth + 0x03) // 0x04)) * max(0x01, ((ddsHeight + 0x03) // 0x04)) * 0x10

        self.currentTexture = Image.open(io.BytesIO(self.fb.read(self.currentSize)))
        self.currentTexture = ImageTk.PhotoImage(self.currentTexture)
        self.textureCanvas.create_image(int(self.textureCanvas.winfo_width()) // 2, int(self.textureCanvas.winfo_height()) // 2, image = self.currentTexture)

    def loadTextureEvent(self, event):
        self.loadTexture()

    def moveTextureEvent(self, event):
        if self.currentTexture is not None:
            self.textureCanvas.delete("all")
            self.textureCanvas.create_image(event.x, event.y, image = self.currentTexture)

    def saveNU20(self):
        filePath = filedialog.asksaveasfile(mode = "wb", initialfile = self.fileName, defaultextension = os.path.splitext(self.fileName)[1], filetypes = (("Bionicle Heroes NU20", "*.nup *.hgp"), ("All Files", "*.*")))

        if filePath:
            self.fb.seek(0x00, os.SEEK_SET)
            filePath.write(self.fb.read())
            filePath.close()

    def extractTexture(self):
        filePath = filedialog.asksaveasfile(mode = "wb", initialfile = str(self.ddsNumber) + ".dds", defaultextension = ".dds", filetypes = (("DDS image", "*.dds"), ("All Files", "*.*")))

        if filePath:
            self.fb.seek(self.ddsLocation, os.SEEK_SET)
            filePath.write(self.fb.read(self.currentSize))
            filePath.close()

    def replaceTexture(self):
        filePath = filedialog.askopenfile(mode = "rb", filetypes = (("DDS image", "*.dds"), ("All Files", "*.*")))

        if filePath:
            magic = struct.unpack("<I", filePath.read(4))[0]

            if magic != 0x20534444:
                msgBox = messagebox.showerror("Error", "Selected file is not a DDS image! It will not be imported!")
                filePath.close()
            else:
                inputSize = self.getFileSize(filePath)

                if inputSize > self.currentSize:
                    msgBox = messagebox.showerror("Error", "Selected DDS size is too large! It will not be imported!")
                    filePath.close()
                else:
                    filePath.seek(0x0C, os.SEEK_CUR)
                    height = struct.unpack("<I", filePath.read(4))[0]
                    width = struct.unpack("<I", filePath.read(4))[0]
                    filePath.seek(0x08, os.SEEK_CUR)
                    mips = struct.unpack("<I", filePath.read(4))[0]
                    self.fb.seek(self.ddsEntry)
                    self.fb.write(struct.pack("<I", width))
                    self.fb.write(struct.pack("<I", height))
                    self.fb.write(struct.pack("<I", mips))
                    filePath.seek(0x00, os.SEEK_SET)
                    fileBytes = filePath.read()
                    filePath.close()
                    self.fb.seek(self.ddsLocation, os.SEEK_SET)
                    self.fb.write(fileBytes)
                    msgBox = messagebox.showinfo("Info", "Texture replaced successfully.")
                    # Call load texture so the change is visible
                    self.loadTexture()

def main():
    root = tk.Tk()
    root.resizable(0, 0)
    gui = NU20Editor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
