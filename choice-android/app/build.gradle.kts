// ============================================================
// Choice Viet Nam Android app build config
// ============================================================
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.choicevietnam.app"

    compileSdk = 35

    defaultConfig {
        applicationId = "com.choicevietnam.app"

        minSdk = 24
        targetSdk = 35

        // Version naming follows AGI-PM convention:
        // V<YYYY.MM.DD>.<daily serial>, starting at 01
        versionCode = 1
        versionName = "V2026.09.11.01"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        create("release") {
            storeFile = file(rootProject.file("choice-release.keystore"))
            storePassword = (project.findProperty("CHOICE_RELEASE_STORE_PASSWORD") as String?) ?: "choice123"
            keyAlias = (project.findProperty("CHOICE_RELEASE_KEY_ALIAS") as String?) ?: "choice"
            keyPassword = (project.findProperty("CHOICE_RELEASE_KEY_PASSWORD") as String?) ?: "choice123"
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("debug")
        }
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("release")
        }
    }

    buildFeatures {
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.webkit:webkit:1.12.1")
    implementation("androidx.swiperefreshlayout:swiperefreshlayout:1.1.0")

    testImplementation("junit:junit:4.13.2")
}
