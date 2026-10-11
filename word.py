import os
import win32com.client


class WordFormatter:
    def __init__(self, visible=True):
        """连接到 Word，并新建一个文档"""
        self.word = win32com.client.Dispatch("Word.Application")
        self.word.Visible = visible
        self.doc = self.word.Documents.Add()

    def add_paragraph(self, text, font_name="Calibri", font_size=11,
                      bold=False, italic=False, underline=False,
                      color_rgb=0, align="left"):
        """
        添加一段文字，并设置统一格式
        """
        para = self.doc.Paragraphs.Add()
        para.Range.Text = text

        # 设置段落对齐
        if align == "left":
            para.Alignment = 0
        elif align == "center":
            para.Alignment = 1
        elif align == "right":
            para.Alignment = 2

        # 设置字体
        para.Range.Font.Name = font_name
        para.Range.Font.Size = font_size
        para.Range.Font.Bold = bold
        para.Range.Font.Italic = italic
        para.Range.Font.Underline = underline
        para.Range.Font.Color = color_rgb

        para.Range.InsertParagraphAfter()
        return para

    def add_text_inline(self, text, font_name="Calibri", font_size=11,
                        bold=False, italic=False, underline=False,
                        color_rgb=0):
        """Append formatted text without inserting a paragraph break."""
        if "\n" in text or "\r" in text:
            raise ValueError("Inline text cannot contain line breaks.")

        start = self.doc.Content.End - 1
        insertion_range = self.doc.Range(start, start)
        insertion_range.InsertAfter(text)

        text_range = self.doc.Range(start, self.doc.Content.End - 1)
        text_range.ParagraphFormat.Alignment = 0  # Left align
        text_range.Font.Name = font_name
        text_range.Font.Size = font_size
        text_range.Font.Bold = bold
        text_range.Font.Italic = italic
        text_range.Font.Underline = underline
        text_range.Font.Color = color_rgb
        return text_range

    def add_line_break(self):
        """Start a new line without adding any text."""
        end = self.doc.Content.End - 1
        self.doc.Range(end, end).InsertAfter("\r")

    def add_title(self, text):
        """添加标题"""
        self.add_paragraph(
            text=text,
            font_name="Calibri",
            font_size=18,
            bold=True,
            color_rgb=0xFF0000,
            align="center"
        )

    def save_as(self, file_path):
        """保存 Word 文件"""
        self.doc.SaveAs(file_path)

    def close(self):
        """关闭 Word"""
        self.doc.Close(SaveChanges=False)
        self.word.Quit()


if __name__ == "__main__":
    # 例子：生成一个 Word 文档
    word_doc = WordFormatter(visible=True)

    word_doc.add_title("Sample Report")
    word_doc.add_paragraph(
        "This is a normal paragraph with fixed font and size.",
        font_name="Calibri",
        font_size=12,
        bold=False,
        italic=False,
        underline=False,
        color_rgb=0
    )

    word_doc.add_paragraph(
        "This is a bold blue paragraph.",
        font_name="Arial",
        font_size=14,
        bold=True,
        italic=False,
        underline=False,
        color_rgb=0xFF0000
    )

    word_doc.add_paragraph(
        "This is italic with a gray color.",
        font_name="Calibri",
        font_size=11,
        bold=False,
        italic=True,
        underline=True,
        color_rgb=0x808080
    )

    # 连续调用 add_text_inline，文字会留在同一段中。
    word_doc.add_text_inline("我很好。", font_size=12, color_rgb=0xFF0000)
    word_doc.add_text_inline("我是谁", font_size=12, color_rgb=0x00FF00)
    word_doc.add_line_break()

    word_doc.add_paragraph(
        "This is italic with a gray color.",
        font_name="Calibri",
        font_size=11,
        bold=False,
        italic=True,
        underline=True,
        color_rgb=0x808080
    )    
