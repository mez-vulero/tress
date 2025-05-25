<template>
  <div v-show="false" />
</template>
<script setup>
const props = defineProps({})

function makeOutgoingCall(number) {
  // placeholder for WebSprix outbound call
  console.log('Calling via WebSprix', number)
}

function setup() {}

defineExpose({ makeOutgoingCall, setup })
</script>
