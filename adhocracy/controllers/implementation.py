import cgi
from datetime import datetime

from pylons.i18n import _
from formencode import foreach, Invalid

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.forms as forms


log = logging.getLogger(__name__)


class ImplementationCreateForm(formencode.Schema):
    allow_extra_fields = True
    page = forms.ValidPage()


class ImplementationController(BaseController):
    
    @RequireInstance
    def index(self, proposal_id, format="html"):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        c.proposal_tile = tiles.proposal.ProposalTile(c.proposal)
        
        return render("/implementation/index.html")
    
    
    @RequireInstance
    def new(self, proposal_id, errors=None):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        defaults = dict(request.params)
        c.proposal_tile = tiles.proposal.ProposalTile(c.proposal)
        return htmlfill.render(render("/implementation/new.html"), defaults=defaults, 
                               errors=errors, force_defaults=False)
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    def create(self, proposal_id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        try:
            self.form_result = ImplementationCreateForm().to_python(request.params)
        except Invalid, i:
            return self.new(proposal_id, errors=i.unpack_errors())
        
        selection = model.Selection.create(c.proposal, self.form_result.get('page'), 
                                           c.user)
        model.meta.Session.commit()
        # TODO implement
        # TODO emit an event 
        return redirect(h.entity_url(c.proposal, member='implementation'))
    

    def edit(self, proposal_id, id, errors={}):
        return self.not_implemented()
    
    
    def update(self, proposal_id, id, format='html'):
        return self.not_implemented()
    
    
    @RequireInstance
    def show(self, proposal_id, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        c.proposal_tile = tiles.proposal.ProposalTile(c.proposal)
        
        return render("/implementation/show.html")
    
    
    @RequireInstance
    def ask_delete(self, proposal_id, id):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        c.proposal_tile = tiles.proposal.ProposalTile(c.proposal)
        
        return render("/implementation/ask_delete.html")
    
    
    @RequireInstance
    @RequireInternalRequest()
    def delete(self, proposal_id, id):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        
        # TODO implement
        
        redirect(h.entity_url(c.proposal))
    