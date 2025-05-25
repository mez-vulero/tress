<template>
  <div v-show="showCallPopup" v-bind="$attrs">
    <div
      ref="callPopup"
      class="fixed z-20 flex w-60 cursor-move select-none flex-col rounded-lg bg-surface-gray-7 p-4 text-ink-gray-2 shadow-2xl"
      :style="style"
    >
      <div class="flex flex-row-reverse items-center gap-1">
        <MinimizeIcon
          class="h-4 w-4 cursor-pointer"
          @click="toggleCallWindow"
        />
      </div>
      <div class="flex flex-col items-center justify-center gap-3">
        <Avatar
          v-if="contact?.image"
          :image="contact.image"
          :label="contact.full_name"
          class="relative flex !h-24 !w-24 items-center justify-center [&>div]:text-[30px]"
          :class="onCall || calling ? '' : 'pulse'"
        />
        <div class="flex flex-col items-center justify-center gap-1">
          <div class="text-xl font-medium">
            {{ contact?.full_name ?? __('Unknown') }}
          </div>
          <div class="text-sm text-ink-gray-5">{{ contact?.mobile_no }}</div>
        </div>
        <CountUpTimer ref="counterUp">
          <div v-if="onCall" class="my-1 text-base">
            {{ counterUp?.updatedTime }}
          </div>
        </CountUpTimer>
        <div v-if="!onCall" class="my-1 text-base">
          {{
            callStatus == 'initiating'
              ? __('Initiating call...')
              : callStatus == 'ringing'
                ? __('Ringing...')
                : calling
                  ? __('Calling...')
                  : __('Incoming call...')
          }}
        </div>
        <div v-if="onCall" class="flex gap-2">
          <Button
            :icon="muted ? 'mic-off' : 'mic'"
            class="rounded-full"
            @click="toggleMute"
          />
          <!-- <Button class="rounded-full">
          <template #icon>
            <DialpadIcon class="cursor-pointer rounded-full" />
          </template>
        </Button> -->
          <Button class="rounded-full">
            <template #icon>
              <NoteIcon
                class="h-4 w-4 cursor-pointer rounded-full text-ink-gray-9"
                @click="showNoteModal = true"
              />
            </template>
          </Button>
          <Button class="rounded-full bg-surface-red-5 hover:bg-surface-red-6">
            <template #icon>
              <PhoneIcon
                class="h-4 w-4 rotate-[135deg] fill-white text-ink-white"
                @click="hangUpCall"
              />
            </template>
          </Button>
        </div>
        <div v-else-if="calling || callStatus == 'initiating'">
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Cancel')"
            @click="cancelCall"
            class="rounded-lg"
            :disabled="callStatus == 'initiating'"
          >
            <template #prefix>
              <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" />
            </template>
          </Button>
        </div>
        <div v-else class="flex gap-2">
          <Button
            size="md"
            variant="solid"
            theme="green"
            :label="__('Accept')"
            class="rounded-lg"
            @click="acceptIncomingCall"
          >
            <template #prefix>
              <PhoneIcon class="h-4 w-4 fill-white" />
            </template>
          </Button>
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Reject')"
            class="rounded-lg"
            @click="rejectIncomingCall"
          >
            <template #prefix>
              <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" />
            </template>
          </Button>
        </div>
      </div>
    </div>
  </div>
  <div
    v-show="showSmallCallWindow"
    class="ml-2 flex cursor-pointer select-none items-center justify-between gap-3 rounded-lg bg-surface-gray-7 px-2 py-[7px] text-base text-ink-gray-2"
    @click="toggleCallWindow"
    v-bind="$attrs"
  >
    <div class="flex items-center gap-2">
      <Avatar
        v-if="contact?.image"
        :image="contact.image"
        :label="contact.full_name"
        class="relative flex !h-5 !w-5 items-center justify-center"
      />
      <div class="max-w-[120px] truncate">
        {{ contact?.full_name ?? __('Unknown') }}
      </div>
    </div>
    <div v-if="onCall" class="flex items-center gap-2">
      <div class="my-1 min-w-[40px] text-center">
        {{ counterUp?.updatedTime }}
      </div>
      <Button variant="solid" theme="red" class="!h-6 !w-6 rounded-full">
        <template #icon>
          <PhoneIcon
            class="h-4 w-4 rotate-[135deg] fill-white"
            @click.stop="hangUpCall"
          />
        </template>
      </Button>
    </div>
    <div v-else-if="calling" class="flex items-center gap-3">
      <div class="my-1">
        {{ callStatus == 'ringing' ? __('Ringing...') : __('Calling...') }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full"
        @click.stop="cancelCall"
      >
        <template #icon>
          <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" />
        </template>
      </Button>
    </div>
    <div v-else class="flex items-center gap-2">
      <Button
        variant="solid"
        theme="green"
        class="pulse relative !h-6 !w-6 rounded-full"
        @click.stop="acceptIncomingCall"
      >
        <template #icon>
          <PhoneIcon class="h-4 w-4 animate-pulse fill-white" />
        </template>
      </Button>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full"
        @click.stop="rejectIncomingCall"
      >
        <template #icon>
          <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" />
        </template>
      </Button>
    </div>
  </div>
  <NoteModal
    v-model="showNoteModal"
    :note="note"
    doctype="CRM Call Log"
    @after="updateNote"
  />
</template>

<script setup>
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CountUpTimer from '@/components/CountUpTimer.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import { UserAgent, Inviter, Invitation, Registerer, SessionState } from 'sip.js'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { Avatar, call, createResource } from 'frappe-ui'
import { ref, watch } from 'vue'

let userAgent = null
let registerer = null
let session = null
let sipDomain = ''
let log = ref('Connecting...')

let showCallPopup = ref(false)
let showSmallCallWindow = ref(false)
let onCall = ref(false)
let calling = ref(false)
let muted = ref(false)
let callPopup = ref(null)
let counterUp = ref(null)
let callStatus = ref('')

const phoneNumber = ref('')

const contact = ref({
  full_name: '',
  image: '',
  mobile_no: '',
})

watch(phoneNumber, (value) => {
  if (!value) return
  getContact.fetch()
})

const getContact = createResource({
  url: 'crm.integrations.api.get_contact_by_phone_number',
  makeParams() {
    return {
      phone_number: phoneNumber.value,
    }
  },
  cache: ['contact', phoneNumber.value],
  onSuccess(data) {
    contact.value = data
  },
})

const showNoteModal = ref(false)
const note = ref({
  name: '',
  title: '',
  content: '',
})

async function updateNote(_note, insert_mode = false) {
  note.value = _note
  if (insert_mode && _note.name) {
    await call('crm.integrations.api.add_note_to_call_log', {
      call_sid: session?.id,
      note: _note,
    })
  }
}

const { width, height } = useWindowSize()

let { style } = useDraggable(callPopup, {
  initialValue: { x: width.value - 280, y: height.value - 310 },
  preventDefault: true,
})

async function startupClient() {
  try {
    const creds = await call('crm.integrations.websprix.api.get_user_settings')
    sipDomain = creds.domain
    const uri = UserAgent.makeURI(`sip:${creds.username}@${creds.domain}`)
    userAgent = new UserAgent({
      uri,
      authorizationUsername: creds.username,
      authorizationPassword: creds.password,
      transportOptions: { server: creds.websocket },
    })
    registerer = new Registerer(userAgent)
    userAgent.delegate = { onInvite: handleIncomingCall }
    await userAgent.start()
    await registerer.register()
    log.value = 'Ready to make and receive calls!'
  } catch (err) {
    log.value = 'An error occurred. ' + err.message
  }
}

function toggleMute() {
  muted.value = !muted.value
  if (session && session.sessionDescriptionHandler) {
    const pc = session.sessionDescriptionHandler.peerConnection
    pc.getSenders().forEach((sender) => {
      if (sender.track) sender.track.enabled = !muted.value
    })
  }
}

function handleIncomingCall(invitation) {
  session = invitation
  phoneNumber.value = invitation.remoteIdentity.uri.user
  showCallPopup.value = true

  session.stateChange.addListener((state) => {
    if (state === SessionState.Established) {
      onCall.value = true
      calling.value = false
      counterUp.value.start()
    } else if (state === SessionState.Terminated) {
      handleDisconnectedIncomingCall()
    }
  })
}

async function acceptIncomingCall() {
  if (!session) return
  await session.accept()
}

function rejectIncomingCall() {
  session?.reject()
  handleDisconnectedIncomingCall()
}

function hangUpCall() {
  session?.bye()
  handleDisconnectedIncomingCall()
}

function handleDisconnectedIncomingCall() {
  showCallPopup.value = false
  if (showSmallCallWindow.value == undefined) {
    showSmallCallWindow = false
  } else {
    showSmallCallWindow.value = false
  }
  session = null
  muted.value = false
  onCall.value = false
  calling.value = false
  callStatus.value = ''
  counterUp.value.stop()
  note.value = { name: '', title: '', content: '' }
}

async function makeOutgoingCall(number) {
  phoneNumber.value = number

  if (!userAgent) {
    log.value = 'Unable to make call.'
    return
  }
  const target = UserAgent.makeURI(`sip:${number}@${sipDomain}`)
  session = new Inviter(userAgent, target)

  session.stateChange.addListener((state) => {
    if (state === SessionState.Establishing) {
      callStatus.value = 'ringing'
    } else if (state === SessionState.Established) {
      onCall.value = true
      calling.value = false
      callStatus.value = 'in-progress'
      counterUp.value.start()
    } else if (state === SessionState.Terminated) {
      handleDisconnectedIncomingCall()
    }
  })

  calling.value = true
  showCallPopup.value = true
  callStatus.value = 'initiating'

  try {
    await session.invite()
  } catch (error) {
    log.value = `Could not connect call: ${error.message}`
  }
}

function cancelCall() {
  session?.cancel()
  handleDisconnectedIncomingCall()
}

function toggleCallWindow() {
  showCallPopup.value = !showCallPopup.value
  if (showSmallCallWindow.value == undefined) {
    showSmallCallWindow = !showSmallCallWindow
  } else {
    showSmallCallWindow.value = !showSmallCallWindow.value
  }
}

defineExpose({ makeOutgoingCall, setup: startupClient })
</script>

<style scoped>
.pulse::before {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
}

.pulse::after {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
  animation-delay: 0.3s;
}

@keyframes pulse {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }

  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}
</style>
