"""This module contains extra callbacks that can add commonly-used functionality to Experiments.
This module also serves as an example for how users can properly construct their own custom
callbacks using :func:`hyperparameter_hunter.callbacks.bases.lambda_callback`

Related
-------
:mod:`hyperparameter_hunter.callbacks.bases`
    This module defines :func:`hyperparameter_hunter.callbacks.bases.lambda_callback`, which is how
    all extra callbacks created in :mod:`hyperparameter_hunter.callbacks.recipes` are created
:mod:`hyperparameter_hunter.environment`
    This module provides the means to use custom callbacks made by
    :func:`hyperparameter_hunter.callbacks.bases.lambda_callback` through the `experiment_callbacks`
    argument of :meth:`hyperparameter_hunter.environment.Environment.__init__`

Notes
-----
For the purposes of aggregating additional Experiment information, this module describes two methods
outlined in :func:`hyperparameter_hunter.callbacks.recipes.confusion_matrix_oof`, and
:func:`hyperparameter_hunter.callbacks.recipes.confusion_matrix_holdout`. The first automatically
handles aggregating new values; whereas, the second provides an example for manually aggregating new
values, which offers greater customization at the cost of slightly more overhead"""
##################################################
# Import Own Assets
##################################################
from hyperparameter_hunter.callbacks.bases import lambda_callback
from hyperparameter_hunter.metrics import get_clean_prediction

##################################################
# Import Miscellaneous Assets
##################################################
import numpy as np
import pandas as pd

##################################################
# Import Learning Assets
##################################################
from sklearn.metrics import confusion_matrix as sk_confusion_matrix


##################################################
# Confusion Matrix Callbacks
##################################################
def confusion_matrix_oof(on_run=True, on_fold=True, on_repetition=True, on_experiment=True):
    """Callback function to produce confusion matrices for out-of-fold predictions at each stage of
    the Experiment

    Parameters
    ----------
    on_run: Boolean, default=True
        If False, skip making confusion matrices for individual Experiment runs
    on_fold: Boolean, default=True
        If False, skip making confusion matrices for individual Experiment folds
    on_repetition: Boolean, default=True
        If False, skip making confusion matrices for individual Experiment repetitions
    on_experiment: Boolean, default=True
        If False, skip making final confusion matrix for the Experiment

    Returns
    -------
    LambdaCallback
        An uninitialized :class:`LambdaCallback` to generate confusion matrices, produced by
        :func:`hyperparameter_hunter.callbacks.bases.lambda_callback`

    Notes
    -----
    Unlike :func:`hyperparameter_hunter.callbacks.recipes.confusion_matrix_holdout`, this callback
    function allows `lambda_callback` to automatically aggregate the stats returned by each of the
    "on..." functions given to `lambda_callback`

    If the size of this `lambda_callback` implementation is daunting, minimize the helper functions'
    docstrings. It's surprisingly simple"""

    # noinspection PyUnusedLocal
    def _on_run_end(data_oof, **kwargs):
        """Callback to execute upon ending an Experiment's run. Note that parameters are
        named after Experiment attributes

        Parameters
        ----------
        data_oof: Dataset
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.data_oof`
        **kwargs: Dict
            If this is given as a parameter to one of `lambda_callback`\'s functions, the entirety
            of the Experiment's attributes will be given as a dict. This can be used for debugging

        Returns
        -------
        Array-like"""
        return _confusion_matrix(data_oof.target.fold, data_oof.prediction.run)

    def _on_fold_end(data_oof, validation_index):
        """Callback to execute upon ending an Experiment's fold. Note that parameters are
        named after Experiment attributes

        Parameters
        ----------
        data_oof: Dataset
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.data_oof`
        validation_index: Array-like
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.validation_index`

        Returns
        -------
        Array-like"""
        return _confusion_matrix(
            data_oof.target.fold, data_oof.prediction.rep.iloc[validation_index]
        )

    def _on_repetition_end(data_train, data_oof):
        """Callback to execute upon ending an Experiment's repetition. Note that parameters are
        named after Experiment attributes

        Parameters
        ----------
        data_train: Dataset
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.data_train`
        data_oof: Dataset
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.data_oof`

        Returns
        -------
        Array-like"""
        # return _confusion_matrix(data_oof.target.final, data_oof.prediction.rep)  # TODO: Should use this when collecting transformed targets
        return _confusion_matrix(data_train.target.d, data_oof.prediction.rep)  # FLAG: TEMPORARY

    def _on_experiment_end(data_train, data_oof):
        """Callback to execute upon ending an Experiment. Note that parameters are
        named after Experiment attributes

        Parameters
        ----------
        data_train: Dataset
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.data_train`
        data_oof: Dataset
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.data_oof`

        Returns
        -------
        Array-like"""
        # return _confusion_matrix(data_oof.target.final, data_oof.prediction.final)  # TODO: Should use this when collecting transformed targets
        return _confusion_matrix(data_train.target.d, data_oof.prediction.final)  # FLAG: TEMPORARY

    return lambda_callback(
        on_run_end=_on_run_end if on_run else None,
        on_fold_end=_on_fold_end if on_fold else None,
        on_repetition_end=_on_repetition_end if on_repetition else None,
        on_experiment_end=_on_experiment_end if on_experiment else None,
        agg_name="confusion_matrix_oof",
    )


def confusion_matrix_holdout(on_run=True, on_fold=True, on_repetition=True, on_experiment=True):
    """Callback function to produce confusion matrices for holdout predictions at each stage of
    the Experiment

    Parameters
    ----------
    on_run: Boolean, default=True
        If False, skip making confusion matrices for individual Experiment runs
    on_fold: Boolean, default=True
        If False, skip making confusion matrices for individual Experiment folds
    on_repetition: Boolean, default=True
        If False, skip making confusion matrices for individual Experiment repetitions
    on_experiment: Boolean, default=True
        If False, skip making final confusion matrix for the Experiment

    Returns
    -------
    LambdaCallback
        An uninitialized :class:`LambdaCallback` to generate confusion matrices, produced by
        :func:`hyperparameter_hunter.callbacks.bases.lambda_callback`

    Notes
    -----
    Unlike :func:`hyperparameter_hunter.callbacks.recipes.confusion_matrix_oof`, this callback
    bypasses `lambda_callback`\'s ability to automatically aggregate stats returned by the "on..."
    functions. It does this simply by not returning values in the "on..." functions, and manually
    aggregating the stats in :attr:`hyperparameter_hunter.experiments.BaseExperiment.stat_aggregates`.
    This offers greater control over how your values are collected, but also requires additional
    overhead, namely, instantiating a dict to collect the values via :func:`_on_experiment_start`.
    Note also that each of the "on..." functions must append their values to an explicitly named
    container in :attr:`hyperparameter_hunter.experiments.BaseExperiment.stat_aggregates` when using
    this method as opposed to :func:`hyperparameter_hunter.callbacks.recipes.confusion_matrix_oof`\'s

    If the size of this `lambda_callback` implementation is daunting, minimize the helper functions'
    docstrings. It's surprisingly simple"""

    def _on_experiment_start(stat_aggregates):
        """Callback to instantiate container for Experiment values to be aggregated

        Parameters
        ----------
        stat_aggregates: Dict
            :attr:`hyperparameter_hunter.experiments.BaseExperiment.stat_aggregates`"""
        stat_aggregates["confusion_matrix_holdout"] = dict(runs=[], folds=[], reps=[], final=None)

    def _on_run_end(stat_aggregates, data_holdout):
        """Callback to execute upon ending an Experiment's run. Note that parameters are
        named after Experiment attributes

        Parameters
        ----------
        stat_aggregates: Dict
            :attr:`hyperparameter_hunter.experiments.BaseExperiment.stat_aggregates`
        data_holdout: Dataset
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.data_holdout`"""
        stat_aggregates["confusion_matrix_holdout"]["runs"].append(
            _confusion_matrix(data_holdout.target.fold, data_holdout.prediction.run)
        )

    def _on_fold_end(stat_aggregates, data_holdout):
        """Callback to execute upon ending an Experiment's fold. Note that parameters are
        named after Experiment attributes

        Parameters
        ----------
        stat_aggregates: Dict
            :attr:`hyperparameter_hunter.experiments.BaseExperiment.stat_aggregates`
        data_holdout: Dataset
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.data_holdout`"""
        stat_aggregates["confusion_matrix_holdout"]["folds"].append(
            _confusion_matrix(data_holdout.target.fold, data_holdout.prediction.fold)
        )

    def _on_repetition_end(stat_aggregates, data_holdout):
        """Callback to execute upon ending an Experiment's repetition. Note that parameters are
        named after Experiment attributes

        Parameters
        ----------
        stat_aggregates: Dict
            :attr:`hyperparameter_hunter.experiments.BaseExperiment.stat_aggregates`
        data_holdout: Dataset
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.data_holdout`"""
        stat_aggregates["confusion_matrix_holdout"]["reps"].append(
            # _confusion_matrix(data_holdout.target.final, data_holdout.prediction.rep)  # TODO: Should use this when collecting transformed targets
            _confusion_matrix(data_holdout.target.d, data_holdout.prediction.rep)  # FLAG: TEMPORARY
        )

    def _on_experiment_end(stat_aggregates, data_holdout):
        """Callback to execute upon ending an Experiment. Note that parameters are
        named after Experiment attributes

        Parameters
        ----------
        stat_aggregates: Dict
            :attr:`hyperparameter_hunter.experiments.BaseExperiment.stat_aggregates`
        data_holdout: Dataset
            :attr:`hyperparameter_hunter.experiments.BaseCVExperiment.data_holdout`"""
        stat_aggregates["confusion_matrix_holdout"]["final"] = _confusion_matrix(
            # data_holdout.target.final, data_holdout.prediction.final  # TODO: Should use this when collecting transformed targets
            data_holdout.target.d,
            data_holdout.prediction.final,  # FLAG: TEMPORARY
        )

    return lambda_callback(
        on_experiment_start=_on_experiment_start,
        on_run_end=_on_run_end if on_run else None,
        on_fold_end=_on_fold_end if on_fold else None,
        on_repetition_end=_on_repetition_end if on_repetition else None,
        on_experiment_end=_on_experiment_end if on_experiment else None,
        agg_name="confusion_matrix_holdout",
    )


def _confusion_matrix(targets, predictions):
    """Helper function to produce a confusion matrix after properly formatting `predictions`

    Parameters
    ----------
    targets: Array-like
        The target/expected output labels for each of the given `predictions`
    predictions: Array-like
        The predicted values corresponding to each of the elements in `targets`

    Returns
    -------
    Array-like
        A confusion matrix for the given `targets` and `predictions`"""
    return sk_confusion_matrix(targets, get_clean_prediction(targets, predictions))


##################################################
# Excessive Recording Callbacks
##################################################
def dataset_recorder(save_transformed=False):
    """Build a `LambdaCallback` that records the current state of all datasets `on_fold_start` and
    `on_fold_end` in order to validate modifications made by
    :class:`feature_engineering.FeatureEngineer`/:class:`feature_engineering.EngineerStep`

    Returns
    -------
    LambdaCallback
        Aggregator-like `LambdaCallback` whose values are aggregated under the name "_datasets" and
        whose keys are named after the corresponding callback methods"""

    def _on_fold(data_train, data_oof, data_holdout, data_test, kwargs):
        d = dict(
            fold_train_input=data_train.input.fold,
            fold_train_target=data_train.target.fold,
            fold_validation_input=None if data_oof is None else data_oof.input.fold,
            fold_validation_target=None if data_oof is None else data_oof.target.fold,
            fold_holdout_input=None if data_holdout is None else data_holdout.input.fold,
            fold_holdout_target=None if data_holdout is None else data_holdout.target.fold,
            fold_test_input=None if data_test is None else data_test.input.fold,
        )
        if save_transformed:
            for k in ["transformed_fold_holdout_target", "transformed_run_validation_target"]:
                if k in kwargs:
                    d[k] = kwargs[k]
        return {k: v if not isinstance(v, pd.DataFrame) else v.copy() for k, v in d.items()}

    return lambda_callback(
        on_fold_start=_on_fold, on_fold_end=_on_fold, agg_name="datasets", method_agg_keys=True
    )


##################################################
# Experiment Description Callbacks
##################################################
# TODO: Add callback recipe to save an Experiment's description file as a yaml file alongside json
# TODO: May need to extend `lambda_callback`'s capabilities to include the result-saving stage
# TODO: ... The final description file likely isn't available at the time `on_experiment_end` called
# FLAG: When done, move this section below the "Confusion Matrix Callbacks" section below
# FLAG: Consider adding option to save Experiment descriptions as yaml by default
# FLAG: ... Will probably need to employ special `--- !!omap` yaml tags (http://yaml.org/spec/1.1/ ["Example 2.26"])

##################################################
# Keras Epochs Elapsed Callback
##################################################
def aggregator_epochs_elapsed(on_run=True, on_fold=True, on_repetition=True, on_experiment=True):
    """Callback function to aggregate and average the number of epochs elapsed during model training
    at each stage of the Experiment

    Parameters
    ----------
    on_run: Boolean, default=True
        If False, skip recording epochs elapsed for individual Experiment runs
    on_fold: Boolean, default=True
        If False, skip making epochs-elapsed averages for individual Experiment folds
    on_repetition: Boolean, default=True
        If False, skip making epochs-elapsed averages for individual Experiment repetitions
    on_experiment: Boolean, default=True
        If False, skip making epochs-elapsed average for the Experiment

    Returns
    -------
    LambdaCallback
        An uninitialized :class:`LambdaCallback` to aggregate the number of epochs elapsed during
        training, produced by :func:`hyperparameter_hunter.callbacks.bases.lambda_callback`"""

    def _on_run_end(model):
        """Return the number of epochs elapsed after fitting model"""
        if model.epochs_elapsed is not None:
            return model.epochs_elapsed

    def _on_fold_end(stat_aggregates, _run):
        """Average the number of epochs elapsed across all runs in the fold"""
        run_results = stat_aggregates["_epochs_elapsed"]["runs"]
        if len(run_results) > 0:
            return np.average(run_results[-_run:])

    def _on_repetition_end(stat_aggregates, _run, _fold):
        """Average the number of epochs elapsed across all runs in the repetition"""
        run_results = stat_aggregates["_epochs_elapsed"]["runs"]
        if len(run_results) > 0:
            num_runs = _run * _fold
            return np.average(run_results[-num_runs:])

    def _on_experiment_end(stat_aggregates, _run, _fold, _rep):
        """Average the number of epochs elapsed across all runs in the Experiment"""
        run_results = stat_aggregates["_epochs_elapsed"]["runs"]
        if len(run_results) > 0:
            num_runs = _run * _fold * _rep
            return np.average(run_results[-num_runs:])

    return lambda_callback(
        on_run_end=_on_run_end if on_run else None,
        on_fold_end=_on_fold_end if on_fold else None,
        on_repetition_end=_on_repetition_end if on_repetition else None,
        on_experiment_end=_on_experiment_end if on_experiment else None,
        agg_name="epochs_elapsed",
    )
