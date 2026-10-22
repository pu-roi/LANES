"""Bounded recipe derivation and preregistered selection, no training."""
from copy import deepcopy
from pathlib import Path
from datetime import datetime,timedelta
import json
import tempfile
import unittest
from unittest.mock import patch

from training.flood_ner.study_recipes import variant_config, choose_recipe
from training.flood_ner import study_recipes as recipes
from spacy.util import load_config


class RecipeTests(unittest.TestCase):
    def test_only_authorized_recipe_fields_change(self):
        base={'system':{'seed':0}, 'nlp':{'pipeline':['ner']},
              'training':{'patience':175, 'max_epochs':30, 'max_steps':1000, 'eval_frequency':35,
                          'dropout':0.1,'optimizer':{'learn_rate':0.001,'L2':0.01},
                          'before_to_disk':{'output':'original','@callbacks':'frozen'}}}
        saved=deepcopy(base)
        for recipe,patience,lr in [('recovery',175,0.001),('A',350,0.001),('B',350,0.0005)]:
            expected=deepcopy(base)
            expected['training']['patience']=patience
            expected['training']['optimizer']['learn_rate']=lr
            expected['training']['before_to_disk']['output']=str(Path('new')/'selected-checkpoint')
            self.assertEqual(variant_config(base,recipe,Path('new')),expected)
        self.assertEqual(base,saved)
        with self.assertRaises(ValueError):variant_config(base,'C',Path('new'))

    def test_original_then_A_then_B_tie_precedence(self):
        for scores,expected in [({'original':.67,'A':.67,'B':.67},'original'),
                                ({'original':.67,'A':.68,'B':.68},'A'),
                                ({'original':.67,'A':.68,'B':.69},'B'),
                                ({'original':.70,'A':.68,'B':.69},'original')]:
            self.assertEqual(choose_recipe(scores),expected)

    def test_missing_nonfinite_and_extra_recipe_scores_refused(self):
        for scores in [{'original':.5,'A':.6}, {'original':.5,'A':float('nan'),'B':.6},
                       {'original':True,'A':.5,'B':.6},{'original':.5,'A':.6,'B':.7,'C':.8}]:
            with self.assertRaises(ValueError):choose_recipe(scores)

    def test_even_rehashed_configuration_cannot_change_an_unapproved_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);prep=root/'prep';prep.mkdir()
            (prep/'manifest.json').write_text('{}')
            (prep/'train-seed-0.cfg').write_text('[system]\nseed=0\n[training]\npatience=175\nmax_epochs=30\n[training.optimizer]\nlearn_rate=0.001\n[training.before_to_disk]\noutput="old"\n')
            study=root/'backend/training/flood_ner/artifacts/study';study.mkdir(parents=True)
            output=study/'runs/A/seed-0'
            cfg=variant_config(load_config(prep/'train-seed-0.cfg'),'A',output)
            path=study/'A.cfg';cfg.to_disk(path)
            value={'schema_version':'lanes-bounded-validation-recipes-v1','recipes':recipes.RECIPES,
                   'implementation_sha256':recipes.digest(Path(recipes.__file__)),'test_predictions_permitted':False,
                   'preparation_sha256':recipes.digest(prep/'manifest.json'),
                   'no_new_training_after':(datetime.now().astimezone()+timedelta(hours=1)).isoformat(),
                   'configs':[{'recipe':'A','seed':0,'config':'A.cfg','output':'runs/A/seed-0','config_sha256':recipes.digest(path)}],
                   'files':{'A.cfg':recipes.digest(path)}}
            (study/'manifest.json').write_text(json.dumps(value))
            with patch.object(recipes,'ROOT',root),patch.object(recipes,'PREPARATION',prep),patch.object(recipes,'validate_inputs',return_value={}):
                self.assertEqual(recipes.validate_trial(study,'A',0,False)['output'],str(output))
                output.mkdir(parents=True)
                with self.assertRaisesRegex(ValueError,'destination must be new'):recipes.validate_trial(study,'A',0)
                cfg['training']['max_epochs']=999;cfg.to_disk(path)
                value['files']['A.cfg']=recipes.digest(path)
                value['configs'][0]['config_sha256']=recipes.digest(path)
                (study/'manifest.json').write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError,'unapproved settings'):recipes.validate_trial(study,'A',0,False)


if __name__ == '__main__':unittest.main()
