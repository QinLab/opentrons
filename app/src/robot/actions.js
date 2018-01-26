// @flow
// robot actions and action types
// action helpers
import {makeActionName} from '../util'
import {tagAction as tagForAnalytics} from '../analytics'
import {_NAME as NAME} from './constants'
import type {
  Mount,
  Slot,
  Axis,
  Direction,
  RobotService,
  ProtocolFile
} from './types'

// TODO(mc, 2017-11-22): rename this function to actionType
const makeRobotActionName = (action) => makeActionName(NAME, action)
const tagForRobotApi = (action) => ({...action, meta: {robotCommand: true}})

type Error = {message: string}

export type ConfirmProbedAction = {
  type: 'robot:CONFIRM_PROBED',
  payload: Mount
}

// TODO(mc, 2018-01-23): NEW ACTION TYPES GO HERE
export type Action =
  | ConfirmProbedAction

// TODO(mc, 2018-01-23): refactor to use type above
//    DO NOT ADD NEW ACTIONS HERE
export const actionTypes = {
  // discovery, connect, and disconnect
  DISCOVER: makeRobotActionName('DISCOVER'),
  DISCOVER_FINISH: makeRobotActionName('DISCOVER_FINISH'),
  ADD_DISCOVERED: makeRobotActionName('ADD_DISCOVERED'),
  REMOVE_DISCOVERED: makeRobotActionName('REMOVE_DISCOVERED'),
  CONNECT: makeRobotActionName('CONNECT'),
  CONNECT_RESPONSE: makeRobotActionName('CONNECT_RESPONSE'),
  DISCONNECT: makeRobotActionName('DISCONNECT'),
  DISCONNECT_RESPONSE: makeRobotActionName('DISCONNECT_RESPONSE'),

  // protocol loading
  SESSION: makeRobotActionName('SESSION'),
  SESSION_RESPONSE: makeRobotActionName('SESSION_RESPONSE'),

  // calibration
  SET_DECK_POPULATED: makeRobotActionName('SET_DECK_POPULATED'),
  SET_CURRENT_LABWARE: makeRobotActionName('SET_CURRENT_LABWARE'),
  SET_CURRENT_INSTRUMENT: makeRobotActionName('SET_CURRENT_INSTRUMENT'),
  PICKUP_AND_HOME: makeRobotActionName('PICKUP_AND_HOME'),
  PICKUP_AND_HOME_RESPONSE: makeRobotActionName('PICKUP_AND_HOME_RESPONSE'),
  DROP_TIP_AND_HOME: makeRobotActionName('DROP_TIP_AND_HOME'),
  DROP_TIP_AND_HOME_RESPONSE: makeRobotActionName('DROP_TIP_AND_HOME_RESPONSE'),
  CONFIRM_TIPRACK: makeRobotActionName('CONFIRM_TIPRACK'),
  CONFIRM_TIPRACK_RESPONSE: makeRobotActionName('CONFIRM_TIPRACK_RESPONSE'),
  // TODO(mc, 2018-01-10): rename MOVE_TO_FRONT to PREPARE_TO_PROBE?
  MOVE_TO_FRONT: makeRobotActionName('MOVE_TO_FRONT'),
  MOVE_TO_FRONT_RESPONSE: makeRobotActionName('MOVE_TO_FRONT_RESPONSE'),
  PROBE_TIP: makeRobotActionName('PROBE_TIP'),
  PROBE_TIP_RESPONSE: makeRobotActionName('PROBE_TIP_RESPONSE'),
  MOVE_TO: makeRobotActionName('MOVE_TO'),
  MOVE_TO_RESPONSE: makeRobotActionName('MOVE_TO_RESPONSE'),
  TOGGLE_JOG_DISTANCE: makeRobotActionName('TOGGLE_JOG_DISTANCE'),
  JOG: makeRobotActionName('JOG'),
  JOG_RESPONSE: makeRobotActionName('JOG_RESPONSE'),
  UPDATE_OFFSET: makeRobotActionName('UPDATE_OFFSET'),
  UPDATE_OFFSET_RESPONSE: makeRobotActionName('UPDATE_OFFSET_RESPONSE'),
  CONFIRM_LABWARE: makeRobotActionName('CONFIRM_LABWARE'),

  // protocol run controls
  RUN: makeRobotActionName('RUN'),
  RUN_RESPONSE: makeRobotActionName('RUN_RESPONSE'),
  PAUSE: makeRobotActionName('PAUSE'),
  PAUSE_RESPONSE: makeRobotActionName('PAUSE_RESPONSE'),
  RESUME: makeRobotActionName('RESUME'),
  RESUME_RESPONSE: makeRobotActionName('RESUME_RESPONSE'),
  CANCEL: makeRobotActionName('CANCEL'),
  CANCEL_RESPONSE: makeRobotActionName('CANCEL_RESPONSE'),

  TICK_RUN_TIME: makeRobotActionName('TICK_RUN_TIME')
}

export const actions = {
  discover () {
    return tagForRobotApi({type: actionTypes.DISCOVER})
  },

  discoverFinish () {
    return {type: actionTypes.DISCOVER_FINISH}
  },

  connect (name: string) {
    return tagForRobotApi({type: actionTypes.CONNECT, payload: {name}})
  },

  connectResponse (error: ?Error) {
    const didError = error != null
    const action = {type: actionTypes.CONNECT_RESPONSE, error: didError}

    if (didError) return {...action, payload: error}

    return tagForAnalytics(action)
  },

  disconnect () {
    return tagForRobotApi({type: actionTypes.DISCONNECT})
  },

  disconnectResponse (error: ?Error) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.DISCONNECT_RESPONSE,
      error: error != null
    }

    if (error) action.payload = error

    return action
  },

  // TODO(mc, 2018-01-23): type RobotService
  addDiscovered (service: RobotService) {
    return {type: actionTypes.ADD_DISCOVERED, payload: service}
  },

  removeDiscovered (name: string) {
    return {type: actionTypes.REMOVE_DISCOVERED, payload: {name}}
  },

  // make new session with protocol file
  session (file: ProtocolFile) {
    return tagForRobotApi({type: actionTypes.SESSION, payload: {file}})
  },

  // TODO(mc, 2018-01-23): type Session (see reducers/session.js)
  sessionResponse (error: ?Error, session: any) {
    const didError = error != null

    return {
      type: actionTypes.SESSION_RESPONSE,
      error: didError,
      payload: !didError
        ? session
        : error
    }
  },

  setDeckPopulated (payload: boolean) {
    return {type: actionTypes.SET_DECK_POPULATED, payload}
  },

  pickupAndHome (instrument: Mount, labware: Slot) {
    return tagForRobotApi({
      type: actionTypes.PICKUP_AND_HOME,
      payload: {instrument, labware}
    })
  },

  pickupAndHomeResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.PICKUP_AND_HOME_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  // TODO(mc, 2017-11-22): dropTipAndHome takes a slot at the moment because
  // this action is performed in the context of confirming a tiprack labware.
  // This is confusing though, so refactor these actions + state-management
  // as necessary
  dropTipAndHome (instrument: Mount, labware: Slot) {
    return tagForRobotApi({
      type: actionTypes.DROP_TIP_AND_HOME,
      payload: {instrument, labware}
    })
  },

  dropTipAndHomeResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.DROP_TIP_AND_HOME_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  // confirm tiprack action drops the tip unless the tiprack is last
  confirmTiprack (instrument: Mount, labware: Slot) {
    return tagForRobotApi({
      type: actionTypes.CONFIRM_TIPRACK,
      payload: {instrument, labware}
    })
  },

  confirmTiprackResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.CONFIRM_TIPRACK_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  moveToFront (instrument: Mount) {
    return tagForRobotApi({
      type: actionTypes.MOVE_TO_FRONT,
      payload: {instrument}
    })
  },

  moveToFrontResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.MOVE_TO_FRONT_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  probeTip (instrument: Mount) {
    return tagForRobotApi({type: actionTypes.PROBE_TIP, payload: {instrument}})
  },

  probeTipResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.PROBE_TIP_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  confirmProbed (instrument: Mount): ConfirmProbedAction {
    return {type: 'robot:CONFIRM_PROBED', payload: instrument}
  },

  moveTo (instrument: Mount, labware: Slot) {
    return tagForRobotApi({
      type: actionTypes.MOVE_TO,
      payload: {instrument, labware}
    })
  },

  moveToResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.MOVE_TO_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  toggleJogDistance () {
    return {type: actionTypes.TOGGLE_JOG_DISTANCE}
  },

  jog (instrument: Mount, axis: Axis, direction: Direction) {
    return tagForRobotApi({
      type: actionTypes.JOG,
      payload: {instrument, axis, direction}
    })
  },

  jogResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.JOG_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  updateOffset (instrument: Mount, labware: Slot) {
    return tagForRobotApi({
      type: actionTypes.UPDATE_OFFSET,
      payload: {instrument, labware}
    })
  },

  updateOffsetResponse (error: ?Error = null, isTiprack: boolean) {
    return {
      type: actionTypes.UPDATE_OFFSET_RESPONSE,
      error: error != null,
      payload: error || {isTiprack}
    }
  },

  confirmLabware (labware: Slot) {
    return {type: actionTypes.CONFIRM_LABWARE, payload: {labware}}
  },

  run () {
    return tagForRobotApi({type: actionTypes.RUN})
  },

  runResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.RUN_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  pause () {
    return tagForRobotApi({type: actionTypes.PAUSE})
  },

  pauseResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.PAUSE_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  resume () {
    return tagForRobotApi({type: actionTypes.RESUME})
  },

  resumeResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.RESUME_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  cancel () {
    return tagForRobotApi({type: actionTypes.CANCEL})
  },

  cancelResponse (error: ?Error = null) {
    const action: {type: string, error: boolean, payload?: Error} = {
      type: actionTypes.CANCEL_RESPONSE,
      error: error != null
    }
    if (error) action.payload = error

    return action
  },

  tickRunTime () {
    return {type: actionTypes.TICK_RUN_TIME}
  }
}