<template>
  <div />
</template>

<script setup>
import { call } from 'frappe-ui'
import { ref } from 'vue'

let userAgent = null
const settings = ref(null)

async function setup() {
  try {
    settings.value = await call('crm.integrations.websprix.api.get_user_settings')
  } catch (e) {
    console.error(e)
  }
}

function makeOutgoingCall(number) {
  console.log('WebSprix call to', number)
}

defineExpose({ setup, makeOutgoingCall })
</script>

