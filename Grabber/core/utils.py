import re

def md_escape(text: str) -> str:
                                                            
    if not text:
        return ""
                                                                         
                          
                 
    return re.sub(r"([\*_`\[\]])", r"\\\1", text)
