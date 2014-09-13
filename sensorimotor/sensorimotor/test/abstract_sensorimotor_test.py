# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import unittest2 as unittest

import numpy
from prettytable import PrettyTable

from sensorimotor.learn_on_one_cell_temporal_memory import (
  InspectLearnOnOneCellTemporalMemory as SensorimotorTemporalMemory)
# Uncomment lines below to use GeneralTemporalMemory
# from sensorimotor.general_temporal_memory import (
#   InspectGeneralTemporalMemory as SensorimotorTemporalMemory)



class AbstractSensorimotorTest(unittest.TestCase):

  VERBOSITY = 1
  DEFAULT_TM_PARAMS = {}
  SEED = 42


  def _init(self, tmOverrides=None):
    """
    Initialize Sensorimotor Temporal Memory, and other member variables.

    :param tmOverrides: overrides for default Temporal Memory parameters
    """
    params = self._computeTMParams(tmOverrides)
    self.tm = SensorimotorTemporalMemory(**params)


  def _feedTM(self, sequence, learn=True):
    sensorSequence, motorSequence, sensorimotorSequence = sequence

    if self.VERBOSITY >= 2:
      table = PrettyTable(["Iteration", "Sensor", "Motor"])
      for i in xrange(len(sensorSequence)):
        sensorPattern = sensorSequence[i]
        motorPattern = motorSequence[i]
        if sensorPattern is None:
          table.add_row([i, "<reset>", "<reset>"])
        else:
          table.add_row([i, list(sensorPattern), list(motorPattern)])
      print "Feeding TM..."
      print table

    self.tm.clearHistory()

    for i in xrange(len(sensorSequence)):
      sensorPattern = sensorSequence[i]
      sensorimotorPattern = sensorimotorSequence[i]
      if sensorPattern is None:
        self.tm.reset()
      else:
        self.tm.compute(sensorPattern,
                        activeExternalCells=sensorimotorPattern,
                        formInternalConnections=False,
                        learn=learn)

    if self.VERBOSITY >= 2:
      print self.tm.prettyPrintHistory(verbosity=self.VERBOSITY-2)
      print

    if learn and self.VERBOSITY >= 3:
      print self.tm.prettyPrintConnections()


  def _testTM(self, sequence):
    sensorSequence, _, _ = sequence

    self._feedTM(sequence, learn=False)
    stats = self.tm.getStatistics()

    self.allStats.append((self.id(), stats))

    return stats


  # ==============================
  # Overrides
  # ==============================

  @classmethod
  def setUpClass(cls):
    cls.allStats = []


  @classmethod
  def tearDownClass(cls):
    cols = ["Test",
            "predicted active cells (stats)",
            "predicted inactive cells (stats)",
            "predicted active columns (stats)",
            "predicted inactive columns (stats)",
            "unpredicted active columns (stats)"]

    table = PrettyTable(cols)

    for stats in cls.allStats:
      row = [stats[0]] + list(stats[1])
      table.add_row(row)

    print
    print table
    print "(stats) => (min, max, sum, average, standard deviation)"


  def setUp(self):
    self.tm = None
    self.tmTestMachine = None
    self._random = numpy.random.RandomState(self.SEED)

    if self.VERBOSITY >= 2:
      print ("\n"
             "======================================================\n"
             "Test: {0} \n"
             "{1}\n"
             "======================================================\n"
      ).format(self.id(), self.shortDescription())


  # ==============================
  # Helper functions
  # ==============================

  @staticmethod
  def _generateSensorimotorSequences(length, worlds, agent):
    """
    @param length (int)           Length of each sequence to generate, one for
                                  each world
    @param worlds (list)          Worlds to act in
    @param agent  (AbstractAgent) Agent acting in worlds

    @return (tuple) (sensor sequence, motor sequence, sensorimotor sequence)
    """
    sensorSequence = []
    motorSequence = []
    sensorimotorSequence = []

    for world in worlds:
      for _ in xrange(length):
        sensorPattern = world.sense()
        motorValue = agent.chooseMotorValue(world)
        motorPattern = world.move(motorValue)
        sensorSequence.append(sensorPattern)
        motorSequence.append(motorPattern)

        sensorimotorPattern = (sensorPattern |
          set([x + world.universe.nSensor for x in motorPattern]))
        sensorimotorSequence.append(sensorimotorPattern)

      sensorSequence.append(None)
      motorSequence.append(None)
      sensorimotorSequence.append(None)

    return (sensorSequence, motorSequence, sensorimotorSequence)


  def _computeTMParams(self, overrides):
    params = dict(self.DEFAULT_TM_PARAMS)
    params.update(overrides or {})
    return params

