# Fixed isolated repair, not a general AsciiDoc cross-reference resolver.
require 'asciidoctor/converter/html5'
require 'json'
require 'digest'
module FixedDynamicRoute19
  IDS = ['dynamic-state-current-value', 'dynamic-state-lifetime'].freeze
  def route_allowed19(node, pages)
    node.type == :xref && node.document.attr?('isrefpage') &&
      pages.key?(File.basename(node.document.attr('docfile').to_s, '.adoc')) &&
      IDS.include?(node.target.to_s.delete_prefix('#')) &&
      node.target.start_with?('#') &&
      !node.document.catalog[:refs].key?(node.target[1..-1])
  end
  def convert_inline_anchor(node)
    result = super
    config = (@route19_config ||= JSON.parse(File.read(File.join(__dir__, 'reference-dynamic-route19.json'))))
    return result unless route_allowed19(node, config.fetch('pages'))
    unless @route19_checked
      root = File.expand_path('..', __dir__)
      config.fetch('sources').each do |path, expected|
        raise 'fixed route source changed' unless Digest::SHA256.file(File.join(root, path)).hexdigest == expected
      end
      doc = node.document.attr('docfile')
      name = File.basename(doc, '.adoc')
      raise 'fixed refpage path' unless File.expand_path(doc) == File.join(root, 'gen/refpage', name + '.adoc')
      raise 'fixed refpage bytes' unless Digest::SHA256.file(doc).hexdigest == config.fetch('pages').fetch(name).fetch('source_sha256')
      spec = File.read(File.join(root, 'gen/out/html/vkspec.html'))
      raise 'fixed full specification bytes' unless Digest::SHA256.hexdigest(spec) == config.fetch('full_spec_html_sha256')
      IDS.each { |id| raise 'unique target anchor' unless spec.scan(/\bid="#{Regexp.escape(id)}"/).length == 1 }
      raise 'fixed reference destination' unless node.document.attr('html_spec_relative') == '../../html/vkspec.html'
      @route19_checked = true
    end
    old = 'href="' + node.target + '"'
    raise 'single converted xref' unless result.scan(old).length == 1
    result.sub(old, 'href="../../html/vkspec.html' + node.target + '"')
  end
end
Asciidoctor::Converter::Html5Converter.prepend(FixedDynamicRoute19)
