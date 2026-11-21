pluginManagement {
    val flutterSdkPath =
        run {
            val properties = java.util.Properties()
            file("local.properties").inputStream().use { properties.load(it) }
            val flutterSdkPath = properties.getProperty("flutter.sdk")
            require(flutterSdkPath != null) { "flutter.sdk not set in local.properties" }
            flutterSdkPath
        }

    includeBuild("$flutterSdkPath/packages/flutter_tools/gradle")

    // Automatically migrate legacy pub-cache plugins (flutter_tts, share_plus) to AGP 9+ Built-in Kotlin
    val pubCacheHosted = java.io.File(System.getProperty("user.home"), ".pub-cache/hosted/pub.dev")
    if (pubCacheHosted.exists()) {
        pubCacheHosted.listFiles()?.forEach { pluginDir ->
            val gradleFile = java.io.File(pluginDir, "android/build.gradle")
            if (gradleFile.exists()) {
                val original = gradleFile.readText()
                var updated = original
                    .replace("apply plugin: 'kotlin-android'\n", "")
                    .replace("apply plugin: \"kotlin-android\"\n", "")
                    .replace(
                        Regex("""kotlinOptions\s*\{\s*jvmTarget\s*=\s*(?:JavaVersion\.VERSION_11|['"]11['"])\s*\}"""),
                        "kotlin {\n        compilerOptions {\n            jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_11\n        }\n    }"
                    )
                    .replace(
                        Regex("""kotlinOptions\s*\{\s*jvmTarget\s*=\s*(?:17|JavaVersion\.VERSION_17|['"]17['"])\s*\}"""),
                        "kotlin {\n        compilerOptions {\n            jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17\n        }\n    }"
                    )
                if (updated != original) {
                    gradleFile.writeText(updated)
                }
            }
        }
    }

    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

plugins {
    id("dev.flutter.flutter-plugin-loader") version "1.0.0"
    id("com.android.application") version "9.3.1" apply false
    id("org.jetbrains.kotlin.android") version "2.4.20" apply false
}

include(":app")
