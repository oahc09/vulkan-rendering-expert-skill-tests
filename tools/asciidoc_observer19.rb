# Observer only: delegates every preprocessing operation to pinned Asciidoctor.
require 'asciidoctor'
require 'json'
require 'digest'
module VulkanObserver19
  def self.emit(row)
    File.open(ENV.fetch('VULKAN_ADOC_TRACE'), 'a') { |f| f.puts(JSON.generate(row)) }
  end
  def self.location(reader)
    c=reader.cursor
    {file:c.file.to_s, line:c.lineno}
  end
  def preprocess_conditional_directive(keyword,target,delimiter,text)
    before=VulkanObserver19.location(self); skip_before=@skipping
    result=super
    VulkanObserver19.emit({kind:'conditional',source:before,keyword:keyword,target:target,delimiter:delimiter,text:text,skipping_before:skip_before,skipping_after:@skipping,result:result})
    result
  end
  def preprocess_include_directive(target,attrlist)
    source=VulkanObserver19.location(self)
    result=super
    VulkanObserver19.emit({kind:'include_directive',source:source,target:target,options:attrlist,result:result})
    result
  end
  def resolve_include_path(target,attrlist,attributes)
    source=VulkanObserver19.location(self)
    result=super
    VulkanObserver19.emit({kind:'resolve',source:source,target:target,options:attrlist,attributes:attributes,resolved:result.is_a?(Array) ? result.map(&:to_s) : result})
    result
  end
  def push_include(data,file=nil,path=nil,lineno=1,attributes={})
    # Preserve String vs Array and exact selected strings, before original normalization.
    source=VulkanObserver19.location(self)
    pieces=data.is_a?(Array) ? data : [data]
    VulkanObserver19.emit({kind:'push_include',source:source,file:file.to_s,path:path,engine_start_line:lineno,attributes:attributes,data_type:data.class.name,selected_pieces:pieces,selected_sha256:Digest::SHA256.hexdigest(JSON.generate(pieces)),whole_file_sha256:(file.is_a?(String) && File.file?(file) ? Digest::SHA256.file(file).hexdigest : nil)})
    super
  end
end
Asciidoctor::PreprocessorReader.prepend(VulkanObserver19)
at_exit do
  VulkanObserver19.emit({kind:'observer_end',ruby:RUBY_VERSION,asciidoctor:Asciidoctor::VERSION,loaded_features:$LOADED_FEATURES.select { |x| File.file?(x) }.map { |x| {path:x,sha256:Digest::SHA256.file(x).hexdigest} }})
end
