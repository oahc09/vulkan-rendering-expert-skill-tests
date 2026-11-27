require "asciidoctor"
require ARGV.fetch(0)
Doc = Struct.new(:refpage, :filename, :refs) do
 def attr?(name);name=='isrefpage' && refpage;end
 def attr(name);filename if name=='docfile';end
 def catalog;{refs:refs};end
end
Node = Struct.new(:type,:document,:target)
gate=Object.new.extend(FixedDynamicRoute19);doc=Doc.new(true,'/fixture/vkCmdDraw.adoc',{});node=Node.new(:xref,doc,'#dynamic-state-lifetime');pages={'vkCmdDraw'=>{}}
raise 'positive' unless gate.route_allowed19(node,pages)
doc.refpage=false;raise 'not reference' if gate.route_allowed19(node,pages);doc.refpage=true
doc.filename='/fixture/unregistered.adoc';raise 'not whitepage' if gate.route_allowed19(node,pages);doc.filename='/fixture/vkCmdDraw.adoc'
doc.refs['dynamic-state-lifetime']=Object.new;raise 'local anchor' if gate.route_allowed19(node,pages);doc.refs.clear
node.target='#other';raise 'unknown id' if gate.route_allowed19(node,pages)
puts 'POSITIVE_AND_FOUR_GUARDS_PASSED_SYNTHETIC_NODE_OBJECTS_REAL_RUBY_MODULE'
