from word import WordFormatter

word_doc = WordFormatter(visible=True)

word_doc.add_title("我的报告")
word_doc.add_text_inline("我很好。", font_size=12, color_rgb=0xFF0000)
word_doc.add_text_inline("我是谁", font_size=12, color_rgb=0x00FF00)
word_doc.add_line_break()
word_doc.add_paragraph("这是新的一段。")

