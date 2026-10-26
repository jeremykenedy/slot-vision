-dontobfuscate
-keep class com.jeremykenedy.reelatrium.** { *; }
-keepclasseswithmembernames class * { native <methods>; }
# Optional JVM debugging agents are unreachable in an Android app.
-dontwarn java.lang.instrument.**
-dontwarn sun.misc.**
# Class-retained nullability annotations do not provide runtime behavior.
-dontwarn androidx.annotation.**
-dontwarn org.jetbrains.annotations.**

# Filament frame history fills these fields through JNI rather than Java writes.
-keepclassmembers class com.google.android.filament.Renderer$FrameInfo { <fields>; }
