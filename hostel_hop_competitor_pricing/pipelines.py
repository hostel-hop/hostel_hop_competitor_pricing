import json
# ---------- old ---------
class JsonWriterPipeline:

    def open_spider(self, spider):
        print("Opening file for writing...")
        self.file = open('result.json', 'w', encoding='utf-8')
        self.file.write('[')  
        self.first_item = True

    def close_spider(self, spider):
        print("Closing file...")
        self.file.write(']') 
        self.file.close()

    def process_item(self, item, spider):
        print("Processing item:", item)
        if not self.first_item:
            self.file.write(',\n')
        self.first_item = False
        line = json.dumps(dict(item), ensure_ascii=False)
        self.file.write(line)
        self.file.flush()  
        return item
