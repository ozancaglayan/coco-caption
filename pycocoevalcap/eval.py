__author__ = 'tylin'
import re

from .tokenizer.ptbtokenizer import PTBTokenizer
from .bleu.bleu import Bleu
from .meteor.meteor import Meteor
from .rouge.rouge import Rouge
from .cider.cider import Cider
from .spice.spice import Spice


class COCOEvalCap:
    def __init__(self, coco, cocoRes):
        self.evalImgs = []
        self.eval = {}
        self.imgToEval = {}
        self.coco = coco
        self.cocoRes = cocoRes
        self.params = {'image_id': coco.getImgIds()}
        self.cleanup_fn = lambda s: re.sub(
            '\s*@-@\s*', '-', s.replace("@@ ", "").replace("@@", ""))

    def postprocess(self, caps):
        for cap in caps:
            cap['caption'] = self.cleanup_fn(cap['caption'])
        return caps

    def evaluate(self, verbose=True):
        imgIds = self.params['image_id']
        gts = {}
        res = {}
        for imgId in imgIds:
            gts[imgId] = self.postprocess(self.coco.imgToAnns[imgId])
            res[imgId] = self.postprocess(self.cocoRes.imgToAnns[imgId])

        # =================================================
        # Set up scorers
        # =================================================
        tokenizer = PTBTokenizer()
        gts = tokenizer.tokenize(gts)
        res = tokenizer.tokenize(res)

        # =================================================
        # Set up scorers
        # =================================================
        scorers = [
            (Bleu(), ["Bleu_1", "Bleu_2", "Bleu_3", "Bleu_4"]),
            (Meteor(), "METEOR"),
            (Rouge(), "ROUGE_L"),
            (Cider(), "CIDEr"),
            #(Spice(), "SPICE"),
        ]

        # =================================================
        # Compute scores
        # =================================================
        score_dict = {}
        for scorer, method in scorers:
            score, scores = scorer.compute_score(gts, res)
            if type(method) == list:
                for sc, scs, m in zip(score, scores, method):
                    self.setEval(sc, m)
                    self.setImgToEvalImgs(scs, list(gts.keys()), m)
                    if verbose:
                        print("{}: {:.3f}".format(m, sc))
                    score_dict[m] = sc
            else:
                self.setEval(score, method)
                self.setImgToEvalImgs(scores, list(gts.keys()), method)
                if verbose:
                    print("{}: {:.3f}".format(method, score))
                score_dict[method] = score
        self.setEvalImgs()

        return score_dict

    def setEval(self, score, method):
        self.eval[method] = score

    def setImgToEvalImgs(self, scores, imgIds, method):
        for imgId, score in zip(imgIds, scores):
            if imgId not in self.imgToEval:
                self.imgToEval[imgId] = {}
                self.imgToEval[imgId]["image_id"] = imgId
            self.imgToEval[imgId][method] = score

    def setEvalImgs(self):
        self.evalImgs = [eval_ for imgId, eval_ in self.imgToEval.items()]
