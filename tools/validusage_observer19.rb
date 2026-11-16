# Observer only; loaded AFTER official quiet include processor, only in VU step.
# Every event is immediately written: upstream extractor uses exit!, no at_exit.
require 'json'
require 'digest'
module ValidUsageObserver19
  def self.emit(row)
    File.open(ENV.fetch('VULKAN_VU_TRACE'), 'a') {|f| f.puts(JSON.generate(row))}
  end
  module Missing
    def process(doc, reader, target, attributes)
      ValidUsageObserver19.emit({'kind'=>'quiet_missing','target'=>target,'attributes'=>attributes})
      super
    end
  end
  module Reader
    def push_include(data, file=nil, path=nil, lineno=1, attributes={})
      pieces=data.is_a?(String) ? [data] : data
      ValidUsageObserver19.emit({'kind'=>'push','file'=>file,'path'=>path,'line'=>lineno,'attributes'=>attributes,'selected_sha256'=>Digest::SHA256.hexdigest(JSON.generate(pieces)), 'whole_sha256'=>File.file?(file.to_s) ? Digest::SHA256.file(file).hexdigest : nil})
      super
    end
    def preprocess_conditional_directive(keyword,target,delimiter,text)
      before=@skipping;result=super
      ValidUsageObserver19.emit({'kind'=>'condition','keyword'=>keyword,'target'=>target,'delimiter'=>delimiter,'text'=>text,'before'=>before,'after'=>@skipping,'result'=>result})
      result
    end
  end
end
ExistsIncludeProcessor.prepend(ValidUsageObserver19::Missing)
Asciidoctor::PreprocessorReader.prepend(ValidUsageObserver19::Reader)
