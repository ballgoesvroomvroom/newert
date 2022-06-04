## lightweight and simple parser for markdown contents to be translated into html document
import re

NBSP = "&nbsp;" ## non-breaking space

"""
TO-DO

All-cleared :)
"""

class Regex:
	## .group(1) is hashtags captured
	## .group(2) is chapter name captured
	## .group(3) is article id
	header = re.compile("^(#+) (.*?)(?: \[(.*)\])?$")

	## use to capture images
	## .group(1) is the image alt text
	## .group(2) is the image src path
	## .group(3) is the image caption (figcaption contents)
	image = re.compile("^!\[(.*?)\]\((.*?)\)\[(.*?)\]$")

	## .group(1) is the link text
	## .group(2) is the link path
	links = re.compile("\[(.*?)\]\((.*?)\)")

	## use to replace backticks with <code> tags
	code = re.compile("`([^`]+?)`")

	## code block; multi-line code block
	codeblock = re.compile("^```$")


	### REPLACEMENTS FOR _safeParse
	amp = re.compile("&(?!nbsp;)")

class Article:
	def __init__(self, id):
		self._content = ["<article id={}>".format(id)] ## store contents line by line

		## states
		self.isSection = False
		self.isCodeblock = False
		self.isEnded = False

	def _wrapBackticks(self, text):
		return Regex.code.sub(r"<code>\1</code>", text)

	def _wrapLinks(self, text):
		return Regex.links.sub(r"<a href=\2>\1</a>", text)

	def _safeParse(self, text):
		## replaces "<", ">" and "&"
		text = text.replace("<", "&lt;").replace(">", "&gt;")
		return Regex.amp.sub("&amp;", text)

	def addHeader(self, headerLevel=1, content="&nbsp;"):
		## headerLevel = 1 for h1
		self._content.append("<h{}>{}</h{}>".format(
			headerLevel,
			content,
			headerLevel
		))

	def addPara(self, content=NBSP):
		## check if context is in code
		if self.isCodeblock:
			print("[ para -> code ]")
			self._content.append(content)
			return

		if len(content) == 0 or content.isspace():
			content = NBSP

		content = self._safeParse(content)

		## adds actual html tags, call ._safeParse(content) before
		content = self._wrapBackticks(content)
		content = self._wrapLinks(content)
		self._content.append("<p>{}</p>".format(content))

	def createSection(self):
		## if self.isSection is True, it will close the current section and open a new one
		if self.isSection:
			self._content.append("</section>")

		self.isSection = True
		self._content.append("<section>")

	def addImage(self, alt="", src="", caption=""):
		## caption is not needed
		self._content.append("<figure>")
		self._content.append("<img src={} alt={}>".format(src, alt))
		self._content.append("<figcaption>{}</figcaption>".format(caption))
		self._content.append("</figure>") ## close figure element

	def addLink(self, text, path):
		self._content.append("<a href={}>{}</a>".format(path, text))

	def createCode(self):
		## toggle self.isCodeblock true if not true yet
		## if self.isCodeblock is already true, closes code context by calling self.endCode()
		if not self.isCodeblock:
			self.isCodeblock = True
			self._content.append("<pre><code>")
		else:
			self.endCode()

	def endCode(self):
		## closes code context
		if not self.isCodeblock:
			print("[ WARNING ]: Calling Article.closeCode even though Article instance is not in code context")
			raise RuntimeError
		else:
			self._content.append("</code></pre>")
			self.isCodeblock = False

	def end(self):
		## close any existing codeblocks if any
		if self.isCodeblock:
			self.closeCode()

		## close section tag
		if self.isSection:
			self._content.append("</section>")

		self._content.append("</article>")

		self.isSection = False
		self.isEnded = True

	def concat(self, baseIndent=0):
		## called after building every line
		## baseIndent can allow you to fit into .html files easily
		self.results = ""

		## keep track of indent level
		indentTriggers = ["article", "section", "figure"]
		indent = -1 +baseIndent ## start from -1 as first element is an article tag which increments one automatically
		indentChar = "\t"

		## local state
		isInCode = False
		openingCode = False ## another set of toggle so indentations are removed on second iteration and not on opening tags

		for linec in range(len(self._content)):
			line = self._content[linec]

			## indent
			isTrigger = False
			for trigger in indentTriggers:
				if trigger in line:
					if line[1] == "/":
						## closing tag
						indent -= 1
					else:
						isTrigger = True ## don't indent opening tag
						indent += 1

			## indent for within <pre><code>
			lineIndent = indentChar *indent
			if line == "<pre><code>":
				isInCode = True
				openingCode = False
			elif line == "</code></pre>":
				isInCode = False
				openingCode = False

			if (line == "</code></pre>") or (linec > 0 and self._content[linec -1] == "<pre><code>"):
				## remove trailing line feed at the end of opening tag
				self.results = self.results[:-1]
			if isInCode and not openingCode:
				openingCode = True
			elif (isInCode and openingCode) or line == "</code></pre>":
				## don't indent this line, codeblock contents follow opening tag right after
				## for closing tag, there should be no indent
				lineIndent = ""
			elif isTrigger:
				lineIndent = lineIndent[:-1] ## remove one indent from triggering tag

			self.results += lineIndent +line +"\n"

		self.results = self.results[:-1] ## remove leading line feed
		return self.results

class Match:
	@staticmethod
	def isHeader(line):
		## return (hashtags, chaptername, articleid) as a tuple if match, else None
		## find for header
		header = Regex.header.match(line)
		if header:
			return header.groups()

	@staticmethod
	def isImage(line):
		## returns (alttext, srcpath, caption) as a tuple if match, else None
		## find for images
		img = Regex.image.match(line)
		if img:
			return img.groups()

	@staticmethod
	def isLink(line):
		## if match, returns a tuple (linkText, linkPath)
		link = Regex.links.match(line)
		if link:
			return link.groups()

	@staticmethod
	def isCode(line):
		## if match, returns an empty tuple
		code = Regex.codeblock.match(line)
		if code:
			return code.groups()
		
if __name__ == "__main__":
	contents = ""
	with open("portfolio_contents.txt", "r") as f:
		contents = f.read()

	## split
	lines = contents.split("\n")

	## store
	currentArticle = None

	## find first header
	for linecount in range(len(lines)):
		line = lines[linecount]

		header = Match.isHeader(line)
		image = Match.isImage(line) if header == None else None
		link = Match.isLink(line) if (header == None and image == None) else None
		codeblock = Match.isCode(line) if (header == None and link == None) else None
		print(line, None if currentArticle == None else currentArticle.isCodeblock)

		header = Match.isHeader(line)
		if header:
			indent, name, articleid = header
			indent = len(indent)

			if indent == 1:
				## new article
				if currentArticle != None:
					currentArticle.end()
				currentArticle = Article(articleid)

				## create new section to host header
				currentArticle.createSection()

				currentArticle.addHeader(1, name)
			else:
				## not a new article, a sub heading instead
				if currentArticle == None:
					## there has to be header
					raise RuntimeError

				## create new section to host header
				currentArticle.createSection()

				currentArticle.addHeader(indent, name)
		elif image:
			alttext, src, caption = image
			currentArticle.addImage(alttext, src, caption)
		elif link:
			text, path = link
			currentArticle.addLink(text, path)
		elif codeblock != None:
			print("CREATING CODE")
			currentArticle.createCode() ## acts as a toggle, state is handled internally
		elif currentArticle != None:
			print("[ normal para ]")
			currentArticle.addPara(line)

	currentArticle.end()

	with open("o.txt", "w") as f:
		f.write(currentArticle.concat(3))
	print("PASTED")
