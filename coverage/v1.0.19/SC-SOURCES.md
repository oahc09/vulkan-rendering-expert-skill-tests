# SC migration audit provenance

sc-core-delta.json is transformed metadata from Khronos Vulkan registry vk.xml,
Copyright2015–2026 The Khronos Group Inc., SPDX Apache-2.0 OR MIT.
Original source: https://github.com/KhronosGroup/Vulkan-Docs/blob/fa30d4e312e843193601be7cb926c7e25d9ec885/xml/vk.xml
Frozen SHA256: d56ff7f1613c36b820998dbd8e184b79ec49dc44db63390185205fa15ebcd444.
Only VKSC_VERSION_1_0 direct require/remove records are extracted; namespace
membership and runtime validity are not inferred from this delta alone.
Original full source is not duplicated. Preserve its attribution/license for
these transformed records; source-path fields locate the original elements.

Actual inspected binary hash is recorded in sc-core-delta.json and matches the
previous transfer-case.json repaired binary. Undefined-symbol scan is read-only.
It does not observe dynamic entry-point resolution or execute SC commands.

Separate normative reservation page accessed 2026-11-15:
https://registry.khronos.org/VulkanSC/specs/1.0-extensions/man/html/VkDeviceObjectReservationCreateInfo.html
Retrieved HTML SHA256 68d119c6479b5a5200d1eb04015f907f43f1327338eaa3e8918144bbf358ade1.
Page is CC-BY-4.0 Khronos content and is not vendored. Online release and frozen
registry are distinct sources; do not label them one complete SC snapshot.
