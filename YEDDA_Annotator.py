# -*- coding: utf-8 -*-
# @Author: Jie Yang from SUTD
# @Date:   2016-Jan-06 17:11:59
# @Last Modified by:   Jie Yang,     Contact: jieynlp@gmail.com
# @Last Modified time: 2018-03-05 17:41:03
#!/usr/bin/env python
# coding=utf-8

from tkinter import *
from tkinter.ttk import * # Frame, Button, Label, Style, Scrollbar
from tkinter import filedialog as tkFileDialog
from tkinter import font as tkFont
from tkinter import messagebox as tkMessageBox

import re
from collections import deque
import pickle
import os.path
import platform
import codecs

from utils.recommend import *


class Example(Frame):
    """TODO 换成更贴切的类名"""
    def __init__(self, parent):
        Frame.__init__(self, parent)
        #u转换为unicode编码
        self.Version = u"SmartNote-V1.0 标注工具-单人标注"
        self.OS = platform.system().lower()
        self.parent = parent
        self.fileName = ""
        self.continueOpen = False
        self.debug = False
        self.colorAllChunk = True
        self.recommendFlag = True
        self.history = deque(maxlen=20)
        self.currentContent = deque(maxlen=1)
        self.pressCommand = {'a':"Artifical",
                             'b':"Event",
                             'c':"Fin-Concept",
                             'd':"Location",
                             'e':"Organization",
                             'f':"Person",
                             'g':"Sector",
                             'h':"Other"
                             }
        self.allKey = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.controlCommand = {'q':"unTag", 'ctrl+z':'undo'}
        self.labelEntryList = []
        self.shortcutLabelList = []
        self.configListLabel = None
        self.configListBox = None
        self.labelEntryColor = {'a':"deepskyblue",
                                'b':"darkorchid",
                                'c':"deeppink",
                                'd':"orange",
                                'e':"lime",
                                'f':"burlywood",
                                'g':"crimson",
                                'h':"gray"
                                }
        # 默认 GUI 显示参数
        #根据默认标签数量大小调整页面布局
        if len(self.pressCommand) > 20:
            self.textRow = len(self.pressCommand)
        else:
            self.textRow = 20
        self.textColumn = 5
        self.tagScheme = "BIO"
        self.onlyNP = False  ## for exporting sequence 
        self.keepRecommend = True        

        '''
		self.seged: 用于导出序列，
		True 用于有词语之间有空格间隔，如英文或已分词的中文，
		False 用于按字分隔，如没有分词的中文
        '''
        self.seged = False  ## False 用于没有分词的中文，True 用于英文或已分词的中文
        self.configFile = "configs/default.config"
        self.entityRe = r'\[\@.*?\#.*?\*\](?!\#)'
        self.insideNestEntityRe = r'\[\@\[\@(?!\[\@).*?\#.*?\*\]\#'
        self.recommendRe = r'\[\$.*?\#.*?\*\](?!\#)'
        self.goldAndrecomRe = r'\[\@.*?\#.*?\*\](?!\#)'
        if self.keepRecommend:
            self.goldAndrecomRe = r'\[[\@\$)].*?\#.*?\*\](?!\#)'
        ## 配置颜色
        self.entityColor = "SkyBlue1"
        self.insideNestEntityColor = "light slate blue"
        self.recommendColor = 'lightgreen'
        self.selectColor = 'light salmon'
        self.textFontStyle = "Times"
        self.initUI()
        
    def initUI(self): 
        """初始化 UI"""
        self.parent.title(self.Version)
        #填充父组件的剩余空间
        self.pack(fill=BOTH, expand=True)
        #使某些行和列可伸缩
        for idx in range(0,self.textColumn):
            self.columnconfigure(idx, weight =2)
        # self.columnconfigure(0, weight=2)
        self.columnconfigure(self.textColumn+2, weight=1)
        self.columnconfigure(self.textColumn+4, weight=1)
        for idx in range(0,16):
            self.rowconfigure(idx, weight =1)
        
        self.lbl = Label(self, text=u"文件：没有打开的文件")
        #“文件标签lb1”左右留5距离，上下留4距离，左对齐
        self.lbl.grid(sticky=W, pady=4, padx=5)
        #定义字体fnt
        self.fnt = tkFont.Font(family=self.textFontStyle,size=self.textRow,weight="bold",underline=0)
        self.text = Text(self, font=self.fnt, selectbackground=self.selectColor)
        self.text.grid(row=1, column=0, columnspan=self.textColumn, rowspan=self.textRow, padx=4, sticky=E+W+S+N)

        self.sb = Scrollbar(self)
        self.sb.grid(row = 1, column = self.textColumn, rowspan = self.textRow, padx=0, sticky = E+W+S+N)
        self.text['yscrollcommand'] = self.sb.set 
        self.sb['command'] = self.text.yview 
        # self.sb.pack()

        abtn = Button(self, text="Open", command=self.onOpen)
        abtn.grid(row=1, column=self.textColumn +1)

        recButton = Button(self, text="RMOn", command=self.setInRecommendModel)
        recButton.grid(row=2, column=self.textColumn +1)

        noRecButton = Button(self, text="RMOff", command=self.setInNotRecommendModel)
        noRecButton.grid(row=3, column=self.textColumn +1)

        ubtn = Button(self, text="ReMap", command=self.renewPressCommand)
        ubtn.grid(row=4, column=self.textColumn +1, pady=4)

        ubtn = Button(self, text="NewMap", command=self.savenewPressCommand)
        ubtn.grid(row=5, column=self.textColumn +1, pady=4)

        exportbtn = Button(self, text="Export", command=self.generateSequenceFile)
        exportbtn.grid(row=6, column=self.textColumn + 1, pady=4)        

        cbtn = Button(self, text="Quit", command=self.quit)
        cbtn.grid(row=7, column=self.textColumn + 1, pady=4)

        dbtn = Button(self, text="Continue", command=self.onOpen2)
        dbtn.grid(row=8, column=self.textColumn +1)

        self.cursorName = Label(self, text="Cursor: ", foreground="Blue", font=(self.textFontStyle, 14, "bold"))
        self.cursorName.grid(row=9, column=self.textColumn +1, pady=4)
        self.cursorIndex = Label(self, text=("row: %s\ncol: %s" % (0, 0)), foreground="red", font=(self.textFontStyle, 14, "bold"))
        self.cursorIndex.grid(row=10, column=self.textColumn + 1, pady=4)

        self.RecommendModelName = Label(self, text="RModel: ", foreground="Blue", font=(self.textFontStyle, 14, "bold"))
        self.RecommendModelName.grid(row=12, column=self.textColumn +1, pady=4)
        self.RecommendModelFlag = Label(self, text=str(self.recommendFlag), foreground="red", font=(self.textFontStyle, 14, "bold"))
        self.RecommendModelFlag.grid(row=13, column=self.textColumn + 1, pady=4)
   

        lbl_entry = Label(self, text=u"命令：")
        lbl_entry.grid(row = self.textRow +1,  sticky = E+W+S+N, pady=4,padx=4)
        self.entry = Entry(self)
        self.entry.grid(row = self.textRow +1, columnspan=self.textColumn + 1, rowspan = 1, sticky = E+W+S+N, pady=4, padx=80)
        self.entry.bind('<Return>', self.returnEnter)
        
        # for press_key in self.pressCommand.keys():
        for idx in range(0, len(self.allKey)):
            press_key = self.allKey[idx]

            # self.text.bind(press_key, lambda event, arg=press_key:self.textReturnEnter(event,arg))
            #按下按键后回车输入
            self.text.bind(press_key, self.textReturnEnter)
            #self.text.bind(press_key, self.commandKey)
            simplePressKey = "<KeyRelease-" + press_key + ">"
            #释放按键后删除输入
            self.text.bind(simplePressKey, self.deleteTextInput)
            if self.OS != "windows":
                controlPlusKey = "<Control-Key-" + press_key + ">"
                self.text.bind(controlPlusKey, self.keepCurrent)
                altPlusKey = "<Command-Key-" + press_key + ">"
                self.text.bind(altPlusKey, self.keepCurrent)

        self.text.bind('<Control-Key-z>', self.backToHistory)
        ## disable the default copy behaivour when right click. For MacOS, right click is button 2, other systems are button3
        self.text.bind('<Button-2>', self.rightClick)
        self.text.bind('<Button-3>', self.rightClick)

        self.text.bind('<Double-Button-1>', self.doubleLeftClick)
        self.text.bind('<ButtonRelease-1>', self.singleLeftClick)

        self.setMapShow()

        self.enter = Button(self, text="Enter", command=self.returnButton)
        self.enter.grid(row=self.textRow +1, column=self.textColumn +1)

    def singleLeftClick(self, event):
        """单击鼠标左键，更新光标索引值"""
        if self.debug:
            print(u"动作追踪：单击鼠标左键")
        #返回光标索引值
        cursor_index = self.text.index(INSERT) 
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s\ncol: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)
    
    def doubleLeftClick(self, event):
        """双击鼠标左键，选择实体 (TODO 还没有实现)"""
        if self.debug:
            print(u"动作追踪：双击鼠标左键")
        pass


    ## Disable right click default copy selection behavior
    def rightClick(self, event):
        if self.debug:
            print(u"动作追踪：点击右键")
        try:
            firstSelection_index = self.text.index(SEL_FIRST)
            cursor_index = self.text.index(SEL_LAST)
            content = self.text.get('1.0',"end-1c")
            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            pass

    def setInRecommendModel(self):
        """开启推荐标注模式"""
        self.recommendFlag = True
        self.RecommendModelFlag.config(text = str(self.recommendFlag))
        tkMessageBox.showinfo("Recommend Model", "Recommend Model has been activated!")

    def setInNotRecommendModel(self):
        """关闭推荐标注模式"""
        self.recommendFlag = False 
        self.RecommendModelFlag.config(text = str(self.recommendFlag))
        content = self.getText()
        content = removeRecommendContent(content,self.recommendRe)
        self.writeFile(self.fileName, content, '1.0')
        tkMessageBox.showinfo("Recommend Model", "Recommend Model has been deactivated!")

    def onOpen(self):
        """打开文件"""
        ftypes = [('all files', '.*'), ('text files', '.txt'), ('ann files', '.ann')]
        dlg = tkFileDialog.Open(self, filetypes = ftypes)
        fl = dlg.show()
        if fl != '':
            self.text.delete("1.0",END)
            text = self.readFile(fl)
            self.text.insert(END, text)
            self.setNameLabel("File: " + fl)
            self.autoLoadNewFile(self.fileName, "1.0")
            # self.setDisplay()
            # self.initAnnotate()
            self.text.mark_set(INSERT, "1.0")
            self.setCursorLabel(self.text.index(INSERT))
  
    def onOpen2 (self):
        """打开文件"""
        try:
            (filepath,tempfilename) = os.path.split(self.fileName)
            (filename1, extension) = os.path.splitext(tempfilename)
            innerCharacter = ''.join(re.findall(r'[A-Za-z]', filename1))
            innerNumber = ''.join(re.findall(r'\d+',filename1))
            f2 = filepath +'/' + innerCharacter + str(int(innerNumber)+1) + extension
            print(f2)
            if f2 != '':
                self.text.delete("1.0",END)
                text = self.readFile(f2)
                self.text.insert(END, text)
                self.setNameLabel("File: " + f2)
                self.autoLoadNewFile(self.fileName, "1.0")
                # self.setDisplay()
                # self.initAnnotate()
                self.text.mark_set(INSERT, "1.0")
                self.setCursorLabel(self.text.index(INSERT))
        except AttributeError:
            tkMessageBox.showerror(u"继续打开文件错误!", '请先在文件夹中打开一个文件')
        except FileNotFoundError:
            f2 = filepath +'/' + innerCharacter + str(int(innerNumber)+1) + extension
            self.fileName = f2
            print('except:'+self.fileName)
            tkMessageBox.showerror(u"继续打开文件错误!", '文件不存在！请继续打开文件或重新选择')


    def readFile(self, filename):
        """读文件"""
        with codecs.open(filename, "rU", encoding='utf-8') as f:
            text = f.read()
            self.fileName = filename
            return text

    def setFont(self, value):
        """设置字体"""
        _family=self.textFontStyle
        _size = value
        _weight="bold"
        _underline=0
        fnt = tkFont.Font(family= _family,size= _size,weight= _weight,underline= _underline)
        Text(self, font=fnt)
    
    def setNameLabel(self, new_file):
        self.lbl.config(text=new_file)

    def setCursorLabel(self, cursor_index):
        if self.debug:
            print("Action Track: setCursorLabel")
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s\ncol: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)

    def returnButton(self):
        if self.debug:
            print("Action Track: returnButton")
        self.pushToHistory()
        # self.returnEnter(event)
        content = self.entry.get()
        self.clearCommand()
        self.executeEntryCommand(content)
        return content

    def returnEnter(self,event):
        if self.debug:
            print("Action Track: returnEnter")
        self.pushToHistory()
        content = self.entry.get()
        self.clearCommand()
        self.executeEntryCommand(content)
        return content

    def textReturnEnter(self,event):
        press_key = event.char
        if self.debug:
            print("Action Track: textReturnEnter")
        self.pushToHistory()
        print("event: ", press_key)
        self.clearCommand()
        self.executeCursorCommand(press_key.lower())
        # self.deleteTextInput()
        return press_key

    def backToHistory(self,event):
        if self.debug:
            print("Action Track: backToHistory")
        if len(self.history) > 0:
            historyCondition = self.history.pop()
            # print("history condition: ", historyCondition)
            historyContent = historyCondition[0]
            # print("history content: ", historyContent)
            cursorIndex = historyCondition[1]
            # print("get history cursor: ", cursorIndex)
            self.writeFile(self.fileName, historyContent, cursorIndex)
        else:
            print(u"历史为空！")
        self.text.insert(INSERT, 'p')   # add a word as pad for key release delete

    def keepCurrent(self, event):
        if self.debug:
            print("Action Track: keepCurrent")
        print("keep current, insert:%s"%(INSERT))
        print("before:", self.text.index(INSERT))
        self.text.insert(INSERT, 'p')
        print("after:", self.text.index(INSERT))

    def clearCommand(self):
        if self.debug:
            print("Action Track: clearCommand")
        self.entry.delete(0, 'end')

    def getText(self):
        textContent = self.text.get("1.0","end-1c")
        return textContent

    def executeCursorCommand(self,command):
        if self.debug:
            print("Action Track: executeCursorCommand")
        content = self.getText()
        print("Command:"+command)
        try:
            firstSelection_index = self.text.index(SEL_FIRST)
            cursor_index = self.text.index(SEL_LAST)
            aboveHalf_content = self.text.get('1.0',firstSelection_index)
            followHalf_content = self.text.get(firstSelection_index, "end-1c")
            selected_string = self.text.selection_get()
            if re.match(self.entityRe,selected_string) != None : 
                ## if have selected entity
                new_string_list = selected_string.strip('[@]').rsplit('#',1)
                new_string = new_string_list[0]
                followHalf_content = followHalf_content.replace(selected_string, new_string, 1)
                selected_string = new_string
                # cursor_index = "%s - %sc" % (cursor_index, str(len(new_string_list[1])+4))
                cursor_index = cursor_index.split('.')[0]+"."+str(int(cursor_index.split('.')[1])-len(new_string_list[1])+4)
            afterEntity_content = followHalf_content[len(selected_string):]

            if command == "q":
                print('q: remove entity label')
            else:
                if len(selected_string) > 0:
                    entity_content, cursor_index = self.replaceString(selected_string, selected_string, command, cursor_index)
            aboveHalf_content += entity_content
            content = self.addRecommendContent(aboveHalf_content, afterEntity_content, self.recommendFlag)
            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            ## not select text
            cursor_index = self.text.index(INSERT)
            [line_id, column_id] = cursor_index.split('.')
            aboveLine_content =  self.text.get('1.0', str(int(line_id)-1) + '.end')
            belowLine_content = self.text.get(str(int(line_id)+1)+'.0', "end-1c")
            line = self.text.get(line_id + '.0', line_id + '.end')
            matched_span =  (-1,-1)
            detected_entity = -1 ## detected entity type:－1 not detected, 1 detected gold, 2 detected recommend
            for match in re.finditer(self.entityRe, line):
                if  match.span()[0]<= int(column_id) & int(column_id) <= match.span()[1]:
                    matched_span = match.span()
                    detected_entity = 1
                    break
            if detected_entity == -1:
                for match in re.finditer(self.recommendRe, line):
                    if  match.span()[0]<= int(column_id) & int(column_id) <= match.span()[1]:
                        matched_span = match.span()
                        detected_entity = 2
                        break
            line_before_entity = line
            line_after_entity = ""
            if matched_span[1] > 0 :
                selected_string = line[matched_span[0]:matched_span[1]]
                if detected_entity == 1:
                    new_string_list = selected_string.strip('[@*]').rsplit('#',1)
                elif detected_entity == 2:
                    new_string_list = selected_string.strip('[$*]').rsplit('#',1)
                new_string = new_string_list[0]
                old_entity_type = new_string_list[1]
                line_before_entity = line[:matched_span[0]]
                line_after_entity =  line[matched_span[1]:]
                selected_string = new_string
                entity_content = selected_string
                cursor_index = line_id + '.'+ str(int(matched_span[1])-(len(new_string_list[1])+4))
                if command == "q":
                    print('q: remove entity label')
                elif command == 'y':
                    print("y: comfirm recommend label")
                    old_key = self.pressCommand.keys()[self.pressCommand.values().index(old_entity_type)]
                    entity_content, cursor_index = self.replaceString(selected_string, selected_string, old_key, cursor_index)
                else:
                    if len(selected_string) > 0:
                        if command in self.pressCommand:
                            entity_content, cursor_index = self.replaceString(selected_string, selected_string, command, cursor_index)
                        else:
                            return
                line_before_entity += entity_content   
            if aboveLine_content != '':
                aboveHalf_content = aboveLine_content+ '\n' + line_before_entity
            else:
                aboveHalf_content =  line_before_entity
                
            if belowLine_content != '':
                followHalf_content = line_after_entity + '\n' + belowLine_content
            else:
                followHalf_content = line_after_entity 
                
            content = self.addRecommendContent(aboveHalf_content, followHalf_content, self.recommendFlag)
            self.writeFile(self.fileName, content, cursor_index)

    def executeEntryCommand(self,command):
        if self.debug:
            print("Action Track: executeEntryCommand")
        if len(command) == 0:
            currentCursor = self.text.index(INSERT)
            newCurrentCursor = str(int(currentCursor.split('.')[0])+1) + ".0"
            self.text.mark_set(INSERT, newCurrentCursor)
            self.setCursorLabel(newCurrentCursor)
        else:
            command_list = decompositCommand(command)
            for idx in range(0, len(command_list)):
                command = command_list[idx]
                if len(command) == 2:
                    select_num = int(command[0])
                    command = command[1]
                    content = self.getText()
                    cursor_index = self.text.index(INSERT)
                    newcursor_index = cursor_index.split('.')[0]+"."+str(int(cursor_index.split('.')[1])+select_num)
                    # print("new cursor position: ", select_num, " with ", newcursor_index, "with ", newcursor_index)
                    selected_string = self.text.get(cursor_index, newcursor_index)
                    aboveHalf_content = self.text.get('1.0',cursor_index)
                    followHalf_content = self.text.get(cursor_index, "end-1c")
                    if command in self.pressCommand:
                        if len(selected_string) > 0:
                            # print("insert index: ", self.text.index(INSERT))
                            followHalf_content, newcursor_index = self.replaceString(followHalf_content, selected_string, command, newcursor_index)
                            content = self.addRecommendContent(aboveHalf_content, followHalf_content, self.recommendFlag)
                            # content = aboveHalf_content + followHalf_content
                    self.writeFile(self.fileName, content, newcursor_index)            

    def deleteTextInput(self,event):
        if self.debug:
            print("Action Track: deleteTextInput")
        get_insert = self.text.index(INSERT)
        print("delete insert:",get_insert)
        insert_list = get_insert.split('.')
        last_insert = insert_list[0] + "." + str(int(insert_list[1])-1)
        get_input = self.text.get(last_insert, get_insert)
        # print("get_input: ", get_input)
        aboveHalf_content = self.text.get('1.0',last_insert)
        followHalf_content = self.text.get(last_insert, "end-1c")
        if len(get_input) > 0: 
            followHalf_content = followHalf_content.replace(get_input, '', 1)
        content = aboveHalf_content + followHalf_content
        self.writeFile(self.fileName, content, last_insert)

    def replaceString(self, content, string, replaceType, cursor_index):
        """替换字符串"""
        if replaceType in self.pressCommand:
            new_string = "[@" + string + "#" + self.pressCommand[replaceType] + "*]" 
            newcursor_index = cursor_index.split('.')[0]+"."+str(int(cursor_index.split('.')[1])+len(self.pressCommand[replaceType])+5)
        else:
            print("Invaild command!")
            print("cursor index: ", self.text.index(INSERT))
            return content, cursor_index
        content = content.replace(string, new_string, 1)
        return content, newcursor_index

    def writeFile(self, fileName, content, newcursor_index):
        """写文件"""
        if self.debug:
                print("Action track: writeFile")

        if len(fileName) > 0:
            new_name = fileName + '.ann' if '.ann' not in fileName else fileName
            with codecs.open(new_name, 'w', encoding='utf-8') as ann_file:
                ann_file.write(content)
            
            # print("Writed to new file: ", new_name)
            self.autoLoadNewFile(new_name, newcursor_index)
            # self.generateSequenceFile()
        else:
            print("Don't write to empty file!")

    def addRecommendContent(self, train_data, decode_data, recommendMode):
        """添加推荐的内容"""
        if not recommendMode:
            content = train_data + decode_data
        else:
            if self.debug:
                print("Action Track: addRecommendContent, start Recommend entity")
            content = maximum_matching(train_data, decode_data)
        return content

    def autoLoadNewFile(self, fileName, newcursor_index):
        """自动加载新文件"""
        if self.debug:
            print("Action Track: autoLoadNewFile")
        if len(fileName) > 0:
            self.text.delete("1.0",END)
            text = self.readFile(fileName)
            self.text.insert("end-1c", text)
            self.setNameLabel("File: " + fileName)
            self.text.mark_set(INSERT, newcursor_index)
            self.text.see(newcursor_index)
            self.setCursorLabel(newcursor_index)
            self.setColorDisplay()            

       
    def setColorDisplay(self):
        if self.debug:
            print("Action Track: setColorDisplay")
        self.text.config(insertbackground='red', insertwidth=4, font=self.fnt)
   
        countVar = StringVar()
        currentCursor = self.text.index(INSERT)
        lineStart = currentCursor.split('.')[0] + '.0'
        lineEnd = currentCursor.split('.')[0] + '.end'
        commandList = []
         
        if self.colorAllChunk:
            for flag in list('abcdefgh'):
                self.text.mark_set("matchStart"+flag, "1.0")
                self.text.mark_set("matchEnd"+flag, "1.0")
                self.text.mark_set("searchLimit"+flag, 'end-1c')
            self.text.mark_set("recommend_matchStart", "1.0")
            self.text.mark_set("recommend_matchEnd", "1.0")
            self.text.mark_set("recommend_searchLimit", 'end-1c')
        else:
            for flag in list('abcdefgh'):
                self.text.mark_set("matchStart"+flag, lineStart)
                self.text.mark_set("matchEnd"+flag, lineStart)
                self.text.mark_set("searchLimit"+flag, lineEnd)
            self.text.mark_set("recommend_matchStart", lineStart)
            self.text.mark_set("recommend_matchEnd", lineStart)
            self.text.mark_set("recommend_searchLimit", lineEnd)
        
        #为标签设置颜色
        for key in self.pressCommand:
            while True:
                pattern = r'\[\@.*?\#' + self.pressCommand[key] + r'\*\](?!\#)'
                self.text.tag_configure("catagory"+key, background=self.labelEntryColor[key])
                pos = self.text.search(pattern, "matchEnd"+key, "searchLimit"+key,  count=countVar, regexp=True)
                if pos =="":
                    break
                self.text.mark_set("matchStart"+key, pos)
                self.text.mark_set("matchEnd"+key, "%s+%sc" % (pos, countVar.get()))
                        
                first_pos = pos
                last_pos = "%s + %sc" %(pos, str(int(countVar.get())))
                    
                exist= False
                comString = self.text.get(first_pos, last_pos)
                for charc in self.pressCommand:
                    commandList.append(charc)
                commandList.remove(key)
                commandList.sort()
                #print(commandList[0:len(commandList)]) 
                for e in commandList:
                    containing = re.search(self.pressCommand[e]+ r'\*\]',comString) 
                    if containing != None:
                        exist = True
                        break
                if exist:
                    self.text.mark_set("matchEnd"+key, "%s+%sc" % (pos, str(1)))
                    commandList.clear()
                    continue
                self.text.tag_add("catagory"+key, first_pos, last_pos)
                commandList.clear()
                
                   
         
        ## color recommend type
        while True:
            self.text.tag_configure("recommend", background=self.recommendColor)
            recommend_pos = self.text.search(self.recommendRe, "recommend_matchEnd" , "recommend_searchLimit",  count=countVar, regexp=True)
            if recommend_pos =="":
                break
            self.text.mark_set("recommend_matchStart", recommend_pos)
            self.text.mark_set("recommend_matchEnd", "%s+%sc" % (recommend_pos, countVar.get()))
            
            first_pos = recommend_pos
            # second_pos = "%s+%sc" % (recommend_pos, str(1))
            last_pos = "%s+%sc" % (recommend_pos, str(int(countVar.get())))
            self.text.tag_add("recommend", first_pos, last_pos)            
        
        ## color the most inside span for nested span, scan from begin to end again  
        if self.colorAllChunk:
            self.text.mark_set("matchStart", "1.0")
            self.text.mark_set("matchEnd", "1.0")
            self.text.mark_set("searchLimit", 'end-1c')
        else:
            self.text.mark_set("matchStart", lineStart)
            self.text.mark_set("matchEnd", lineStart)
            self.text.mark_set("searchLimit", lineEnd)
        while True:
            self.text.tag_configure("insideEntityColor", background=self.insideNestEntityColor)
            pos = self.text.search(self.insideNestEntityRe , "matchEnd" , "searchLimit",  count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))
            first_pos = "%s + %sc" %(pos, 2)
            last_pos = "%s + %sc" %(pos, str(int(countVar.get())-1))
            self.text.tag_add("insideEntityColor", first_pos, last_pos)   
    
    def pushToHistory(self):
        if self.debug:
            print("Action Track: pushToHistory")
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print("push to history cursor: ", cursorPosition)
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    def pushToHistoryEvent(self,event):
        if self.debug:
            print("Action Track: pushToHistoryEvent")
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print("push to history cursor: ", cursorPosition)
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    def renewPressCommand(self):
        ## 更新快捷方式映射表
        if self.debug:
            print("Action Track: renewPressCommand")
        seq = 0
        new_dict = {}
        listLength = len(self.labelEntryList)
        delete_num = 0
        for key in sorted(self.pressCommand):
            label = self.labelEntryList[seq].get()
            if len(label) > 0:
                new_dict[key] = label
            else: 
                delete_num += 1
            seq += 1
        self.pressCommand = new_dict
        for idx in range(1, delete_num+1):
            self.labelEntryList[listLength-idx].delete(0,END)
            self.shortcutLabelList[listLength-idx].config(text="NON= ") 
        with open(self.configFile, 'wb') as fp:
            pickle.dump(self.pressCommand, fp)
        self.setMapShow()
        tkMessageBox.showinfo("Remap Notification", u"快捷方式已更新！\n\n配置文件保存在：" + self.configFile)

## save as new shortcut map
    def savenewPressCommand(self):
        if self.debug:
            print("Action Track: savenewPressCommand")
        seq = 0
        new_dict = {}
        listLength = len(self.labelEntryList)
        delete_num = 0
        for key in sorted(self.pressCommand):
            label = self.labelEntryList[seq].get()
            if len(label) > 0:
                new_dict[key] = label
            else:
                delete_num += 1
            seq += 1
        self.pressCommand = new_dict
        for idx in range(1, delete_num+1):
            self.labelEntryList[listLength-idx].delete(0,END)
            self.shortcutLabelList[listLength-idx].config(text="NON= ")
        # prompt to ask configFile name
        self.configFile = tkFileDialog.asksaveasfilename(initialdir="./configs/",
                                                         title="Save New Config",
                                                         filetypes=(("YEDDA configs", "*.config"), ("all files", "*.*")))
        # change to relative path following self.init()
        self.configFile = os.path.relpath(self.configFile)
        # make sure ending with ".config"
        if not self.configFile.endswith(".config"):
            self.configFile += ".config"
        with open(self.configFile, 'wb') as fp:
            pickle.dump(self.pressCommand, fp)
        self.setMapShow()
        tkMessageBox.showinfo("Save New Map Notification", "Shortcut map has been saved and updated!\n\nConfigure file has been saved in File:" + self.configFile)


    def setMapShow(self):
        """显示快捷方式映射表"""
        if os.path.isfile(self.configFile):
            with open (self.configFile, 'rb') as fp:
                self.pressCommand = pickle.load(fp)
        hight = len(self.pressCommand)
        width = 2
        row = 0

        mapLabel = Label(self, text =u"快捷键", foreground="blue", font=(self.textFontStyle, 14, "bold"))
        mapLabel.grid(row=0, column = self.textColumn +2,columnspan=2, rowspan = 1, padx = 10)
        
        # destroy all previous widgets before switching shortcut maps
        if self.labelEntryList is not None and type(self.labelEntryList) is type([]):
            for x in self.labelEntryList:
                x.destroy()
        if self.shortcutLabelList is not None and type(self.shortcutLabelList) is type([]):
            for x in self.shortcutLabelList:
                x.destroy()
        self.labelEntryList = []
        self.shortcutLabelList = []
        
        for key in sorted(self.pressCommand):
            row += 1
            # print("key: ", key, "  command: ", self.pressCommand[key])
            symbolLabel = Label(self, text =key.upper() + ": ", foreground="blue", font=(self.textFontStyle, 14, "bold"))
            symbolLabel.grid(row=row, column = self.textColumn +2,columnspan=1, rowspan = 1, padx = 3)
            self.shortcutLabelList.append(symbolLabel)

            labelEntry = Entry(self, foreground=self.labelEntryColor[key], font=(self.textFontStyle, 14, "bold"))
            labelEntry.insert(0, self.pressCommand[key])
            labelEntry.grid(row=row, column = self.textColumn +3, columnspan=1, rowspan = 1)
            self.labelEntryList.append(labelEntry)
            # print("row: ", row)

        if self.configListLabel is not None:
            self.configListLabel.destroy()
        if self.configListBox is not None:
            self.configListBox.destroy()
        self.configListLabel = Label(self, text="Map Templates", foreground="blue", font=(self.textFontStyle, 14, "bold"))
        self.configListLabel.grid(row=row + 1, column=self.textColumn + 2, columnspan=2, rowspan=1, padx=10)
        self.configListBox = Combobox(self, values=getConfigList(), state='readonly')
        self.configListBox.grid(row=row + 2, column=self.textColumn + 2, columnspan=2, rowspan=1, padx=6)
        # select current config file
        self.configListBox.set(self.configFile.split(os.sep)[-1])
        self.configListBox.bind('<<ComboboxSelected>>', self.on_select)

    def on_select(self, event=None):
        if event and self.debug:
            print("Change shortcut map to: ", event.widget.get())
        self.configFile = os.path.join("configs", event.widget.get())
        self.setMapShow()

    def getCursorIndex(self):
        return self.text.index(INSERT)

    def generateSequenceFile(self):
        """生成序列标注文件"""
        if (".ann" not in self.fileName) and (".txt" not in self.fileName): 
            out_error = u"导出功能只能用于 .ann 或 .txt 文件。"
            print(out_error)
            tkMessageBox.showerror(u"导出错误!", out_error)
            return -1
			
        with codecs.open(self.fileName, 'rU', encoding='utf-8') as f:
            fileLines = f.readlines()
        
        lineNum = len(fileLines)
        new_filename = self.fileName.split('.ann')[0]+ '.anns'
        with codecs.open(new_filename, 'w', encoding='utf-8') as seqFile: 
            for line in fileLines:
                if len(line) <= 2:
                    seqFile.write('\n')
                    continue
                else:
                    if not self.keepRecommend:
                        line = removeRecommendContent(line, self.recommendRe)
                    wordTagPairs = getWordTagPairs(line, self.seged, self.tagScheme, self.onlyNP, self.goldAndrecomRe)
                    for wordTag in wordTagPairs:
                        seqFile.write(wordTag)
                    ## use null line to seperate sentences
                    seqFile.write('\n')

        print(u"导出序列标注文件：", new_filename)
        print(u"行数：", lineNum)
        showMessage =  u"导出文件成功！\n\n"   
        showMessage += u"格式：" + self.tagScheme + "\n\n"
        showMessage += u"推荐：" + str(self.keepRecommend) + "\n\n"
        showMessage += u"分词：" + str(self.seged) + "\n\n"
        showMessage += u"行数：" + str(lineNum) + "\n\n"
        showMessage += u"文件：" + new_filename
        tkMessageBox.showinfo(u"导出信息", showMessage)


def getConfigList():
    fileNames = os.listdir("./configs")
    filteredFileNames = sorted(filter(lambda x: (not x.startswith(".")) and (x.endswith(".config")), fileNames))
    return list(filteredFileNames)		


def getWordTagPairs(tagedSentence, seged=True, tagScheme="BMES", onlyNP=False, entityRe=r'\[\@.*?\#.*?\*\]'):
    newSent = tagedSentence.strip('\n')
    filterList = re.findall(entityRe, newSent)
    newSentLength = len(newSent)
    chunk_list = []
    start_pos = 0
    end_pos = 0
    if len(filterList) == 0:
        singleChunkList = []
        singleChunkList.append(newSent)
        singleChunkList.append(0)
        singleChunkList.append(len(newSent))
        singleChunkList.append(False)
        chunk_list.append(singleChunkList)
        # print(singleChunkList)
        singleChunkList = []
    else:
        for pattern in filterList:
            # print(pattern)
            singleChunkList = []
            start_pos = end_pos + newSent[end_pos:].find(pattern)
            end_pos = start_pos + len(pattern)
            singleChunkList.append(pattern)
            singleChunkList.append(start_pos)
            singleChunkList.append(end_pos)
            singleChunkList.append(True)
            chunk_list.append(singleChunkList)
            singleChunkList = []
    ## chunk_list format:
    full_list = []
    for idx in range(0, len(chunk_list)):
        if idx == 0:
            if chunk_list[idx][1] > 0:
                full_list.append([newSent[0:chunk_list[idx][1]], 0, chunk_list[idx][1], False])
                full_list.append(chunk_list[idx])
            else:
                full_list.append(chunk_list[idx])
        else:
            if chunk_list[idx][1] == chunk_list[idx-1][2]:
                full_list.append(chunk_list[idx])
            elif chunk_list[idx][1] < chunk_list[idx-1][2]:
                print("ERROR: found pattern has overlap!", chunk_list[idx][1], ' with ', chunk_list[idx-1][2])
            else:
                full_list.append([newSent[chunk_list[idx-1][2]:chunk_list[idx][1]], chunk_list[idx-1][2], chunk_list[idx][1], False])
                full_list.append(chunk_list[idx])

        if idx == len(chunk_list) - 1 :
            if chunk_list[idx][2] > newSentLength:
                print("ERROR: found pattern position larger than sentence length!")
            elif chunk_list[idx][2] < newSentLength:
                full_list.append([newSent[chunk_list[idx][2]:newSentLength], chunk_list[idx][2], newSentLength, False])
            else:
                continue
    return turnFullListToOutputPair(full_list, seged, tagScheme, onlyNP)

	
def turnFullListToOutputPair(fullList, seged=True, tagScheme="BMES", onlyNP=False):
    pairList = []
    for eachList in fullList:
        if eachList[3]:
            contLabelList = eachList[0].strip('[@$]').rsplit('#', 1)
            if len(contLabelList) != 2:
                print("Error: sentence format error!")
            label = contLabelList[1].strip('*')
            if seged:
                contLabelList[0] = contLabelList[0].split()
            if onlyNP:
                label = "NP"
            outList = outputWithTagScheme(contLabelList[0], label, tagScheme)
            for eachItem in outList:
                pairList.append(eachItem)
        else:
            if seged:
                eachList[0] = eachList[0].split()
            for idx in range(0, len(eachList[0])):
                basicContent = eachList[0][idx]
                if basicContent == ' ': 
                    continue
                pair = basicContent + ' ' + 'O\n'
                #pairList.append(pair)
                pairList.append(pair)
    return pairList

	
def outputWithTagScheme(input_list, label, tagScheme="BMES"):
    output_list = []
    list_length = len(input_list)
    if tagScheme=="BMES":
        if list_length ==1:
            pair = input_list[0]+ ' ' + 'S-' + label + '\n'
            output_list.append(pair)
        else:
            for idx in range(list_length):
                if idx == 0:
                    pair = input_list[idx]+ ' ' + 'B-' + label + '\n'
                elif idx == list_length -1:
                    pair = input_list[idx]+ ' ' + 'E-' + label + '\n'
                else:
                    pair = input_list[idx]+ ' ' + 'M-' + label + '\n'
                output_list.append(pair)
    else:
        for idx in range(list_length):
            if idx == 0:
                pair = input_list[idx]+ ' ' + 'B-' + label + '\n'
            else:
                pair = input_list[idx]+ ' ' + 'I-' + label + '\n'
            output_list.append(pair)
    return output_list

	
def removeRecommendContent(content, recommendRe = r'\[\$.*?\#.*?\*\](?!\#)'):
    """删除推荐标注的内容"""
    output_content = ""
    last_match_end = 0
    for match in re.finditer(recommendRe, content):
        matched =content[match.span()[0]:match.span()[1]]
        words = matched.strip('[$]').split("#")[0]
        output_content += content[last_match_end:match.span()[0]] + words
        last_match_end = match.span()[1]
    output_content += content[last_match_end:]
    return output_content

	
def decompositCommand(command_string):
    command_list = []
    each_command = []
    num_select = ''
    for idx in range(0, len(command_string)):
        if command_string[idx].isdigit():
            num_select += command_string[idx]
        else:
            each_command.append(num_select)
            each_command.append(command_string[idx])
            command_list.append(each_command)
            each_command = []
            num_select =''
    # print(command_list)
    return command_list
	

def main():
    print(u"启动 SmartNote 标注工具！")
    print((u"操作系统：%s")%(platform.system()))
    root = Tk()
    #界面大小，及初始位置（左，上）
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (1300/2)
    y = (hs/2) - (700/2)
    root.geometry("1300x700+%d+%d" % (x, y))
    app = Example(root)
    #跳转到自定义函数设置字体大小
    app.setFont(17)
    root.mainloop()


if __name__ == '__main__':
    main()