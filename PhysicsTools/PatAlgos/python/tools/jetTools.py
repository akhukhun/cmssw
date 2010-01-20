import FWCore.ParameterSet.Config as cms

from PhysicsTools.PatAlgos.tools.helpers import *


def patchJetCorrFactors_(jetCorrFactors, newAlgo):
    """
    ------------------------------------------------------------------
    Patch to be called from:
       * switchJECSet_
       * switchJECParameters
    This function can safely be removed as soon as the L7Parton
    corrections for AK5 and AK7 are available.

    jetCorrFactors : jetCorrFactors module
    ------------------------------------------------------------------
    """
    if (newAlgo == "AK5"):
        ## voice a note to the user
        print "NOTE TO USER: L7Parton is currently taken from SC5 instead of AK5 "
        print "              This is an intermediate solution for the time being."
        ## redirect the L7Parton correction in case of AK5 or AK7
        corrLevels = getattr(jetCorrFactors, 'corrLevels').value()
        corrLevels.L7Parton = corrLevels.L7Parton.value().replace(newAlgo, 'SC5')
    if (newAlgo == "AK7"):
        ## voice a note to the user
        print "NOTE TO USER: L7Parton is currently taken from SC7 instead of AK7 "
        print "              This is an intermediate solution for the time being."
        ## redirect the L7Parton correction in case of AK5 or AK7        
        corrLevels = getattr(jetCorrFactors, 'corrLevels').value()
        corrLevels.L7Parton = corrLevels.L7Parton.value().replace(newAlgo, 'SC7')

def switchJECSet(process,
                 newName
                 ):
    """
    ------------------------------------------------------------------
    replace tags in the JetCorrFactorsProducer for end-users:

    process : process
    newName : new correction sample
    ------------------------------------------------------------------    
    """
    jetCorrFactors = getattr(process, 'jetCorrFactors')
    jetCorrFactors.corrSample = newName

def switchJECParameters(jetCorrFactors,
                        newAlgo,
                        newType="Calo",
                        oldAlgo="AK5",
                        oldType="Calo"
                        ):
    """
    ------------------------------------------------------------------    
    replace tags in the JetCorrFactorsProducer

    jetCorrFactors : jetCorrFactors module
    newAlgo        : label of new jet algo [AK5,  SC5,   KT6, ...]
    newType        : label of new jet type [Calo, Pflow, Jpt, ...]
    oldAlgo        : label of old jet alog [AK5,  SC5,   KT6, ...]
    oldType        : label of old jet type [Calo, Pflow, Jpt, ...]
    ------------------------------------------------------------------    
    """
    ## check jet correction steps; the L5Flavor step
    ## is not in the list as it is NOT dependent on 
    ## the specific jet algorithm according to JetMET

    ## do the replacement, the first replacement is newAlgo and newType (as for 
    ## L2 and L3) the second repleacement is for newAlgo only (as for L5 and L7)
    def setCorrLevel(corrLevel):
        if (corrLevel != "none"):
            return corrLevel.value().replace(oldAlgo+oldType,newAlgo+newType).replace(oldAlgo,newAlgo)

    ## get the parameters and change it's attributes for L1 to L7
    corrLevels = getattr(jetCorrFactors, 'corrLevels').value()
    corrLevels.L1Offset   = setCorrLevel(corrLevels.L1Offset  )
    corrLevels.L2Relative = setCorrLevel(corrLevels.L2Relative)
    corrLevels.L3Absolute = setCorrLevel(corrLevels.L3Absolute)
    corrLevels.L4EMF      = setCorrLevel(corrLevels.L4EMF     )
    corrLevels.L6UE       = setCorrLevel(corrLevels.L6UE      )
    corrLevels.L7Parton   = setCorrLevel(corrLevels.L7Parton  )
    ##
    ## patch the jetCorrFactors untill the L7Parton corrections are not available yet
    ##
    patchJetCorrFactors_(jetCorrFactors, newAlgo)    

def runBTagging(process,
                jetCollection,
                label
                ) :
    """
    ------------------------------------------------------------------        
    define sequence to run b tagging on AOD input for a given jet
    collection including a JetTracksAssociatorAtVertex module with
    name 'jetTracksAssociatorAtVertex' + 'label'

    process       : process       
    jetCollection : input jet collection
    label         : postfix label to identify new sequence/modules

    return value is a pair of (sequence, labels) where 'sequence' is
    the cms.Sequence, and 'labels' is a vector with the following
    entries:
     * labels['jta']      = the name of the JetTrackAssociator module
     * labels['tagInfos'] = a list of names of the TagInfo modules
     * labels['jetTags '] = a list of names of the JetTag modules
    ------------------------------------------------------------------        
    """    
    if (label == ''):
        ## label is not allowed to be empty
        raise ValueError, "label for re-running b tagging is not allowed to be empty"        

    ## import track associator & b tag configuration
    process.load("RecoJets.JetAssociationProducers.ak5JTA_cff")
    from RecoJets.JetAssociationProducers.ak5JTA_cff import ak5JetTracksAssociatorAtVertex
    process.load("RecoBTag.Configuration.RecoBTag_cff")
    import RecoBTag.Configuration.RecoBTag_cff as btag

    # add negative tag infos
    import PhysicsTools.PatAlgos.recoLayer0.bTagging_cff as nbtag
    
    ## define jetTracksAssociator; for switchJetCollection
    ## the label is 'AOD' as empty labels will lead to crashes
    ## of crab. In this case the postfix label is skiped,
    ## otherwise a postfix label is added as for the other
    ## labels
    jtaLabel = 'jetTracksAssociatorAtVertex'

    if (not label == 'AOD'):
        jtaLabel  += label
    ## define tag info labels (compare with jetProducer_cfi.py)        
    ipTILabel = 'impactParameterTagInfos'     + label
    svTILabel = 'secondaryVertexTagInfos'     + label
   #nvTILabel = 'secondaryVertexNegativeTagInfos'     + label
    seTILabel = 'softElectronTagInfos'        + label
    smTILabel = 'softMuonTagInfos'            + label
    
    ## produce tag infos
    setattr( process, ipTILabel, btag.impactParameterTagInfos.clone(jetTracks = cms.InputTag(jtaLabel)) )
    setattr( process, svTILabel, btag.secondaryVertexTagInfos.clone(trackIPTagInfos = cms.InputTag(ipTILabel)) )
   #setattr( process, nvTILabel, nbtag.secondaryVertexNegativeTagInfos.clone(trackIPTagInfos = cms.InputTag(ipTILabel)) )
    setattr( process, seTILabel, btag.softElectronTagInfos.clone(jets = jetCollection) )
    setattr( process, smTILabel, btag.softMuonTagInfos.clone(jets = jetCollection) )

    ## make VInputTag from strings
    def vit(*args) : return cms.VInputTag( *[ cms.InputTag(x) for x in args ] )
    
    ## produce btags
    setattr( process, 'jetBProbabilityBJetTags'+label, btag.jetBProbabilityBJetTags.clone(tagInfos = vit(ipTILabel)) )
    setattr( process, 'jetProbabilityBJetTags' +label, btag.jetProbabilityBJetTags.clone (tagInfos = vit(ipTILabel)) )
    setattr( process, 'trackCountingHighPurBJetTags'+label, btag.trackCountingHighPurBJetTags.clone(tagInfos = vit(ipTILabel)) )
    setattr( process, 'trackCountingHighEffBJetTags'+label, btag.trackCountingHighEffBJetTags.clone(tagInfos = vit(ipTILabel)) )
    setattr( process, 'simpleSecondaryVertexBJetTags'+label, btag.simpleSecondaryVertexBJetTags.clone(tagInfos = vit(svTILabel)) )
   #setattr( process, 'simpleSecondaryVertexNegativeBJetTags'+label, nbtag.simpleSecondaryVertexNegativeBJetTags.clone(tagInfos = vit(nvTILabel)) )
    setattr( process, 'combinedSecondaryVertexBJetTags'+label, btag.combinedSecondaryVertexBJetTags.clone(tagInfos = vit(ipTILabel, svTILabel)) )
    setattr( process, 'combinedSecondaryVertexMVABJetTags'+label, btag.combinedSecondaryVertexMVABJetTags.clone(tagInfos = vit(ipTILabel, svTILabel)) )
    setattr( process, 'softElectronByPtBJetTags'+label, btag.softElectronByPtBJetTags.clone(tagInfos = vit(seTILabel)) )
    setattr( process, 'softElectronByIP3dBJetTags'+label, btag.softElectronByIP3dBJetTags.clone(tagInfos = vit(seTILabel)) )
    setattr( process, 'softMuonBJetTags'+label, btag.softMuonBJetTags.clone(tagInfos = vit(smTILabel)) )
    setattr( process, 'softMuonByPtBJetTags'+label, btag.softMuonByPtBJetTags.clone(tagInfos = vit(smTILabel)) )
    setattr( process, 'softMuonByIP3dBJetTags'+label, btag.softMuonByIP3dBJetTags.clone(tagInfos = vit(smTILabel)) )
    
    ## define vector of (output) labels
    labels = { 'jta'      : jtaLabel, 
               'tagInfos' : (ipTILabel,svTILabel,seTILabel,smTILabel), 
               'jetTags'  : [ (x + label) for x in ('jetBProbabilityBJetTags',
                                                    'jetProbabilityBJetTags',
                                                    'trackCountingHighPurBJetTags',
                                                    'trackCountingHighEffBJetTags',
                                                    'simpleSecondaryVertexBJetTags',
                                                   #'simpleSecondaryVertexNegativeBJetTags',
                                                    'combinedSecondaryVertexBJetTags',
                                                    'combinedSecondaryVertexMVABJetTags',
                                                    'softElectronByPtBJetTags',
                                                    'softElectronByIP3dBJetTags',
                                                    'softMuonBJetTags',
                                                    'softMuonByPtBJetTags',
                                                    'softMuonByIP3dBJetTags'
                                                    )
                              ]
               }

    ## extend an existing sequence by otherLabels
    def mkseq(process, firstlabel, *otherlabels):
       seq = getattr(process, firstlabel)
       for x in otherlabels: seq += getattr(process, x)
       return cms.Sequence(seq)

    ## add tag infos to the process
    setattr( process, 'btaggingTagInfos'+label, mkseq(process, *(labels['tagInfos']) ) )
    ## add b tags to the process
    setattr( process, 'btaggingJetTags'+label,  mkseq(process, *(labels['jetTags'])  ) )
    ## add a combined sequence to the process
    seq = mkseq(process, 'btaggingTagInfos'+label, 'btaggingJetTags' + label) 
    setattr( process, 'btagging'+label, seq )
    ## return the combined sequence and the labels defined above
    return (seq, labels)
        
def addJetCollection(process,
                     jetCollection,
                     algoLabel,
                     typeLabel,
                     doJTA        = True,
                     doBTagging   = True,
                     jetCorrLabel = None,
                     doType1MET   = True,
                     doL1Cleaning = True,                     
                     doL1Counters = False,
                     genJetCollection=cms.InputTag("ak5GenJets"),
                     doJetID      = True,
                     jetIdLabel   = "ak5",
                     standardAlgo = "AK5",
                     standardType = "Calo"
                     ):
    """
    ------------------------------------------------------------------        
    add a new collection of jets. Takes the configuration from the
    already configured standard jet collection as starting point;
    replaces before calling addJetCollection will also affect the
    new jet collections

    process          : process
    jetCollection    : input jet collection    
    algoLabel        : label to indicate the jet algorithm (e.g.'AK5')
    typeLabel        : label to indicate the type of constituents (e.
                       g. 'Calo', 'Pflow', 'Jpt', ...)    
    doBTagging       : run b tagging sequence for new jet collection
                       and add it to the new pat jet collection
    doJTA            : run JetTracksAssociation and JetCharge and add
                       it to the new pat jet collection (will autom.
                       be true if doBTagging is set to true)
    jetCorrLabel     : algorithm and type of JEC; use 'None' for no
                       JEC; examples are ('AK5','Calo'), ('SC7',
                       'Calo'), ('KT4','PF')
    doType1MET       : make also a new MET collection (not yet
                       implemented?)
    doL1Cleaning     : copy also the producer modules for cleanPatCands
                       will be set to 'True' automatically when
                       doL1Counters is 'True'
    doL1Counters     : copy also the filter modules that accept/reject
                       the event looking at the number of jets                       
    genJetCollection : GenJet collection to match to

    doJetId          : add jetId variables to the added jet collection?

    jetIdLabel       : specify the label prefix of the xxxJetID object;
                       in general it is the jet collection tag like ak5,
                       kt4 sc5, aso. For more information have a look
                       to SWGuidePATTools#add_JetCollection
    standardAlgo     : standard algorithm label of the collection from
                       which the clones for the new jet collection will
                       be taken from (note that this jet collection has
                       to be available in the event before hand)
    standardType     : standard constituent type label of the collec-
                       tion from which the clones for the new jet
                       collection will be taken from (note that this
                       jet collection has to be available in the event
                       before hand)                       
    ------------------------------------------------------------------                     
    """
    ## define common label for pre pat jet 
    ## creation steps in makePatJets    
 #label=standardAlgo+standardType

    ## create old module label from standardAlgo
    ## and standardType and return
    def oldLabel(prefix=''):        
        return jetCollectionString(prefix, '', '')

    ## create new module label from old module
    ## label and return
    def newLabel(oldLabel):
        newLabel=oldLabel
        if(oldLabel.find(standardAlgo)>=0 and oldLabel.find(standardType)>=0):
            oldLabel=oldLabel.replace(standardAlgo, algoLabel).replace(standardType, typeLabel)
        else:
            oldLabel=oldLabel+algoLabel+typeLabel
        return oldLabel

    ## clone module and add it to the patDefaultSequence
    def addClone(hook, **replaceStatements):
        ## create a clone of the hook with corresponding
        ## parameter replacements
        newModule = getattr(process, hook).clone(**replaceStatements)
        ## add the module to the sequence
        addModuleToSequence(hook, newModule)

    ## add module to the patDefaultSequence
    def addModuleToSequence(hook, newModule):
        hookModule = getattr(process, hook)
        ## add the new module with standardAlgo &
        ## standardType replaced in module label
        setattr( process, newLabel(hook), newModule)
        ## add new module to default sequence
        ## just behind the hookModule
        process.patDefaultSequence.replace( hookModule, hookModule*newModule )        

    ## add a clone of patJets
    addClone(oldLabel(), jetSource = jetCollection)
    ## add a clone of selectedPatJets    
    addClone(oldLabel('selected'), src=cms.InputTag(newLabel(oldLabel())))
    ## add a clone of cleanPatJets    
    if( doL1Cleaning ):
        addClone(oldLabel('clean'), src=cms.InputTag(newLabel(oldLabel('selected'))))
    ## add a clone of countPatJets    
    if( doL1Counters ):
        if( doL1Cleaning ):
            addClone(oldLabel('count'), src=cms.InputTag(newLabel(oldLabel('clean'))))
        else:
            addClone(oldLabel('count'), src=cms.InputTag(newLabel(oldLabel('selected'))))            

    ## get attributes of new module
    l1Jets = getattr(process, newLabel(oldLabel()))

    ## add a clone of gen jet matching
    addClone('patJetPartonMatch', src = jetCollection)
    addClone('patJetGenJetMatch', src = jetCollection, matched = genJetCollection)

    ## add a clone of parton and flavour associations
    addClone('patJetPartonAssociation', jets = jetCollection)
    addClone('patJetFlavourAssociation', srcByReference = cms.InputTag(newLabel('patJetPartonAssociation')))

    ## fix label for input tag
    def fixInputTag(x): x.setModuleLabel(newLabel(x.moduleLabel))
    ## fix label for vector of input tags
    def fixVInputTag(x): x[0].setModuleLabel(newLabel(x[0].moduleLabel))

    ## provide allLayer1Jet inputs with individual labels
    fixInputTag(l1Jets.genJetMatch)
    fixInputTag(l1Jets.genPartonMatch)
    fixInputTag(l1Jets.JetPartonMapSource)

    ## make VInputTag from strings 
    def vit(*args) : return cms.VInputTag( *[ cms.InputTag(x) for x in args ] )

    if (doJTA or doBTagging):
        ## add clone of jet track association        
        process.load("RecoJets.JetAssociationProducers.ak5JTA_cff")
        from RecoJets.JetAssociationProducers.ak5JTA_cff import ak5JetTracksAssociatorAtVertex
        ## add jet track association module to processes
        jtaLabel = 'jetTracksAssociatorAtVertex'+algoLabel+typeLabel
        setattr( process, jtaLabel, ak5JetTracksAssociatorAtVertex.clone(jets = jetCollection) )
        process.makePatJets.replace(process.patJetCharge, getattr(process,jtaLabel)+process.patJetCharge)
        l1Jets.trackAssociationSource = cms.InputTag(jtaLabel)
        addClone('patJetCharge', src=cms.InputTag(jtaLabel)),
        fixInputTag(l1Jets.jetChargeSource)
    else:
        ## switch embedding of track association and jet
        ## charge estimate to 'False'        
        l1Jets.addAssociatedTracks = False
        l1Jets.addJetCharge = False

    if (doBTagging):
        ## define postfixLabel
        postfixLabel=algoLabel+typeLabel
        ## add b tagging sequence
        (btagSeq, btagLabels) = runBTagging(process, jetCollection, postfixLabel)
        ## add b tagging sequence before running the allLayer1Jets modules
        process.makePatJets.replace(getattr(process,jtaLabel), getattr(process,jtaLabel)+btagSeq)
        ## replace corresponding tags for pat jet production
        l1Jets.trackAssociationSource = cms.InputTag(btagLabels['jta'])
        l1Jets.tagInfoSources = cms.VInputTag( *[ cms.InputTag(x) for x in btagLabels['tagInfos'] ] )
        l1Jets.discriminatorSources = cms.VInputTag( *[ cms.InputTag(x) for x in btagLabels['jetTags']  ] )
    else:
        ## switch general b tagging info switch off
        l1Jets.addBTagInfo = False
        
    if (doJetID):
        l1Jets.addJetID = cms.bool(True)
        jetIdLabelNew = jetIdLabel + 'JetID'
        l1Jets.jetIDMap = cms.InputTag( jetIdLabelNew )
    else :
        l1Jets.addJetID = cms.bool(False)

    if (jetCorrLabel != None):
        ## add clone of jet energy corrections;
        ## catch a couple of exceptions first
        if (jetCorrLabel == False ):
            raise ValueError, "In addJetCollection 'jetCorrLabel' must be set to 'None', not 'False'"
        if (jetCorrLabel == "None"):
            raise ValueError, "In addJetCollection 'jetCorrLabel' must be set to 'None' (without quotes)"
        ## check for the correct format
        if type(jetCorrLabel) != type(('AK5','Calo')): 
            raise ValueError, "In switchJetCollection 'jetCorrLabel' must be 'None', or of type ('Algo','Type')"

        ## add clone of jetCorrFactors
        addClone('patJetCorrFactors', jetSource = jetCollection)
        switchJECParameters( getattr(process,newLabel('patJetCorrFactors')), jetCorrLabel[0], jetCorrLabel[1], oldAlgo='AK5',oldType='Calo' )
        fixVInputTag(l1Jets.jetCorrFactorsSource)

        ## switch type1MET corrections off for PFJets
        if( jetCollection.__str__().find('PFJets')>=0 ):
            print '================================================='
            print 'Type1MET corrections are switched off for PFJets.'
            print 'Users are recommened to use pfMET together with'
            print 'PFJets.'
            print '================================================='            
            doType1MET=False

        ## add a clone of the type1MET correction for the new jet collection
        if (doType1MET):
            ## in case there is no jet correction service in the paths add it
            ## as L2L3 if possible, as combined from L2 and L3 otherwise
            if not hasattr( process, 'L2L3JetCorrector%s%s' % jetCorrLabel ):
                setattr( process, 
                         'L2L3JetCorrector%s%s' % jetCorrLabel, 
                         cms.ESSource("JetCorrectionServiceChain",
                                      correctors = cms.vstring('L2RelativeJetCorrector%s%s' % jetCorrLabel,
                                                               'L3AbsoluteJetCorrector%s%s' % jetCorrLabel),
                                      label= cms.string('L2L3JetCorrector%s%s' % jetCorrLabel)
                                      )
                         )
            ## add a clone of the type1MET correction
            ## and the following muonMET correction  
            addClone('metJESCorAK5CaloJet', inputUncorJetsLabel = jetCollection.value(),
                     corrector = cms.string('L2L3JetCorrector%s%s' % jetCorrLabel)
                     )
            addClone('metJESCorAK5CaloJetMuons', uncorMETInputTag = cms.InputTag(newLabel('metJESCorAK5CaloJet')))
            addClone('patMETs', metSource = cms.InputTag(newLabel('metJESCorAK5CaloJetMuons')))
            l1MET = getattr(process, newLabel('patMETs'))
            ## add new met collections output to the pat summary
            process.patCandidateSummary.candidates += [ cms.InputTag(newLabel('patMETs')) ]
    else:
        ## switch jetCorrFactors off
        l1Jets.addJetCorrFactors = False

def switchJetCollection(process,
                        jetCollection,
                        doJTA            = True,
                        doBTagging       = True,
                        jetCorrLabel     = None,
                        doType1MET       = True,
                        genJetCollection = cms.InputTag("ak5GenJets"),
                        doJetID          = True,
                        jetIdLabel       = "ak5"
                        ):
    """
    ------------------------------------------------------------------        
    switch the collection of jets in PAT from the default value to a
    new jet collection

    process          : process
    jetCollection    : input jet collection
    doBTagging       : run b tagging sequence for new jet collection
                       and add it to the new pat jet collection
    doJTA            : run JetTracksAssociation and JetCharge and add
                       it to the new pat jet collection (will autom.
                       be true if doBTagging is set to true)
    jetCorrLabel     : algorithm and type of JEC; use 'None' for no
                       JEC; examples are ('AK5','Calo'), ('SC7',
                       'Calo'), ('KT4','PF')
    doType1MET       : if jetCorrLabel is not 'None', set this to
                       'True' to redo the Type1 MET correction for
                       the new jet colllection; at the moment it must
                       be 'False' for non CaloJets otherwise the
                       JetMET POG module crashes.
    doJetID          : run jet id for new jet collection and add it
                       to the new pat jet collection
    genJetCollection : GenJet collection to match to

    doJetId          : add jetId variables to the added jet collection?

    jetIsLabel       : specify the label prefix of the xxxJetID object;
                       in general it is the jet collection tag like ak5,
                       kt4 sc5, aso. For more informatrino have a look
                       to SWGuidePATTools#switch_JetCollection
                       
    ------------------------------------------------------------------        
    """
    ## save label of old input jet collection
    oldLabel = process.patJets.jetSource;
    
    ## replace input jet collection for generator matches
    process.patJetPartonMatch.src        = jetCollection
    process.patJetGenJetMatch.src        = jetCollection
    process.patJetGenJetMatch.matched    = genJetCollection
    process.patJetPartonAssociation.jets = jetCollection
    ## replace input jet collection for pat jet production
    process.patJets.jetSource         = jetCollection
    
    ## make VInputTag from strings
    def vit(*args) : return cms.VInputTag( *[ cms.InputTag(x) for x in args ] )

    if (doJTA or doBTagging):
        ## replace jet track association
        process.load("RecoJets.JetAssociationProducers.ak5JTA_cff")
        from RecoJets.JetAssociationProducers.ak5JTA_cff import ak5JetTracksAssociatorAtVertex
        process.jetTracksAssociatorAtVertex = ak5JetTracksAssociatorAtVertex.clone(jets = jetCollection)
        process.makePatJets.replace(process.patJetCharge, process.jetTracksAssociatorAtVertex+process.patJetCharge)
        process.patJetCharge.src = 'jetTracksAssociatorAtVertex'
        process.patJets.trackAssociationSource = 'jetTracksAssociatorAtVertex'
    else:
        ## remove the jet track association from the std
        ## sequence
        process.makePatJets.remove(process.patJetCharge)
        ## switch embedding of track association and jet
        ## charge estimate to 'False'
        process.patJets.addAssociatedTracks = False
        process.patJets.addJetCharge = False

    if (doBTagging):
        ## replace b tagging sequence; add postfix label 'AOD' as crab will
        ## crash when confronted with empy labels
        (btagSeq, btagLabels) = runBTagging(process, jetCollection, 'AOD')
        ## add b tagging sequence before running the allLayer1Jets modules
        process.makePatJets.replace(process.jetTracksAssociatorAtVertex, process.jetTracksAssociatorAtVertex+btagSeq)

        ## replace corresponding tags for pat jet production
        process.patJets.trackAssociationSource = btagLabels['jta']
        process.patJets.tagInfoSources = cms.VInputTag( *[ cms.InputTag(x) for x in btagLabels['tagInfos'] ] )
        process.patJets.discriminatorSources = cms.VInputTag( *[ cms.InputTag(x) for x in btagLabels['jetTags']  ] )
    else:
        ## remove b tagging from the std sequence
        process.makePatJets.remove(process.secondaryVertexNegativeTagInfos)
        process.makePatJets.remove(process.simpleSecondaryVertexNegativeBJetTags)
        ## switch embedding of b tagging for pat
        ## jet production to 'False'
        process.patJets.addBTagInfo = False

    if (doJetID):
        jetIdLabelNew = jetIdLabel + 'JetID'
        process.patJets.jetIDMap = cms.InputTag( jetIdLabelNew )
    else:
        process.patJets.addJetID = cms.bool(False)


    if (jetCorrLabel!=None):
        ## replace jet energy corrections; catch
        ## a couple of exceptions first
        if (jetCorrLabel == False ):
            raise ValueError, "In switchJetCollection 'jetCorrLabel' must be set to 'None', not 'False'"
        if (jetCorrLabel == "None"):
            raise ValueError, "In switchJetCollection 'jetCorrLabel' must be set to 'None' (without quotes)"
        ## check for the correct format
        if (type(jetCorrLabel)!=type(('AK5','Calo'))): 
            raise ValueError, "In switchJetCollection 'jetCorrLabel' must be 'None', or of type ('Algo','Type')"

        ## switch JEC parameters to the new jet collection
        process.patJetCorrFactors.jetSource = jetCollection            
        switchJECParameters(process.patJetCorrFactors, jetCorrLabel[0], jetCorrLabel[1], oldAlgo='AK5',oldType='Calo')

        ## switch type1MET corrections off for PFJets
        if( jetCollection.__str__().find('PFJets')>=0 ):
            print '================================================='
            print 'Type1MET corrections are switched off for PFJets.'
            print 'Users are recommened to use pfMET together with'
            print 'PFJets.'
            print '================================================='            
            doType1MET=False

        ## redo the type1MET correction for the new jet collection
        if (doType1MET):
            ## in case there is no jet correction service in the paths add it
            ## as L2L3 if possible, as combined from L2 and L3 otherwise
            if (not hasattr( process, 'L2L3JetCorrector%s%s' % jetCorrLabel )):
                setattr( process, 
                         'L2L3JetCorrector%s%s' % jetCorrLabel, 
                         cms.ESSource("JetCorrectionServiceChain",
                                      correctors = cms.vstring('L2RelativeJetCorrector%s%s' % jetCorrLabel,
                                                               'L3AbsoluteJetCorrector%s%s' % jetCorrLabel),
                                      label = cms.string('L2L3JetCorrector%s%s' % jetCorrLabel)
                                      )
                         )
            ## configure the type1MET correction the following muonMET
            ## corrections have the corMetType1Icone5 as input and are
            ## automatically correct  
            process.metJESCorAK5CaloJet.inputUncorJetsLabel = jetCollection.value()
            process.metJESCorAK5CaloJet.corrector = 'L2L3JetCorrector%s%s' % jetCorrLabel
    else:
        ## remove the jetCorrFactors from the std sequence
        process.patJetMETCorrections.remove(process.jetCorrFactors)
        ## switch embedding of jetCorrFactors off
        ## for pat jet production
        process.patJets.addJetCorrFactors = False
 
def addJetID(process,
             jetSrc,
             jetIdTag
             ):
    """
    ------------------------------------------------------------------
    compute jet id for process

    process : process
    jetIdTag: Tag to append to jet id map
    ------------------------------------------------------------------    
    """
    jetIdLabel = jetIdTag + 'JetID'
    print "Making new jet ID label with label " + jetIdTag

    ## replace jet id sequence
    process.load("RecoJets.JetProducers.ak5JetID_cfi")
    setattr( process, jetIdLabel, process.ak5JetID.clone(src = jetSrc))
    process.makePatJets.replace( process.patJetPartonMatch, getattr(process,jetIdLabel) + process.patJetPartonMatch )

def setTagInfos(process,
                coll = "allLayer1Jets",
                tagInfos = cms.vstring( )
                ):
    """
    ------------------------------------------------------------------    
    replace tag infos for collection jetSrc

    process       : process
    jetCollection : jet collection to set tag infos for
    tagInfos      : tag infos to set
    ------------------------------------------------------------------    
    """
    found = False
    newTags = cms.VInputTag()
    iNewTags = 0
    for k in tagInfos :
        for j in getattr( process, coll ).tagInfoSources :
            vv = j.value();
            if ( vv.find(k) != -1 ):
                found = True
                newTags.append( j )
                
    if not found:
        raise RuntimeError,"""
        Cannot replace tag infos in jet collection""" % (coll)
    else :
        getattr(process,coll).tagInfoSources = newTags
